#!/usr/bin/env python3
"""
Agnos Health Forum Scraper
A professional web scraper for extracting medical forum data from Agnos Health website.
Supports incremental updates, data aggregation, and analytics.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import argparse
import os
import sys
from datetime import datetime
from urllib.parse import urljoin, unquote
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
import hashlib


class AgnosForumScraper:
    """Professional scraper for Agnos Health forums with update and aggregation capabilities."""
    
    def __init__(self, 
                 base_url: str = "https://www.agnoshealth.com",
                 max_threads: int = 20,
                 delay: float = 1.0,
                 output_file: str = "forum_data.jsonl"):
        """
        Initialize the scraper with configuration.
        
        Args:
            base_url: Base URL of the website
            max_threads: Maximum number of threads to scrape
            delay: Delay between requests in seconds
            output_file: Output filename for scraped data
        """
        self.base_url = base_url
        self.max_threads = max_threads
        self.delay = delay
        self.output_file = output_file
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        self.existing_data = {}
        self.existing_thread_ids = set()
        self.stats = defaultdict(int)
        
    def clean_text(self, text: Optional[str]) -> str:
        """Remove extra spaces and newlines from text."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()
    
    def parse_thai_date(self, date_str: str) -> Optional[datetime]:
        """Parse Thai date format (e.g., '2/16/2024')."""
        try:
            return datetime.strptime(date_str, "%m/%d/%Y")
        except:
            try:
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    return datetime(int(year), int(month), int(day))
            except:
                return None
    
    def generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate a unique hash for content to detect duplicates."""
        unique_str = f"{content.get('thread_id')}_{content.get('content', '')[:100]}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def load_existing_data(self) -> None:
        """Load existing data to avoid duplicates during updates."""
        if os.path.exists(self.output_file):
            print(f"Loading existing data from {self.output_file}...")
            with open(self.output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        content_hash = self.generate_content_hash(data)
                        self.existing_data[content_hash] = data
                        # Track thread IDs for faster lookup
                        thread_id = data.get('thread_id')
                        if thread_id:
                            self.existing_thread_ids.add(str(thread_id))
                    except json.JSONDecodeError:
                        continue
            print(f"Loaded {len(self.existing_data)} existing records")
            print(f"Found {len(self.existing_thread_ids)} unique existing threads")
    
    def is_thread_new(self, thread_id: str) -> bool:
        """Check if a thread is new (not already scraped)."""
        return str(thread_id) not in self.existing_thread_ids
    
    def get_new_threads_only(self, all_threads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter to only include new threads that haven't been scraped."""
        new_threads = []
        for thread in all_threads:
            thread_id = thread.get('thread_id')
            if thread_id and self.is_thread_new(thread_id):
                new_threads.append(thread)
        return new_threads
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into smaller chunks for embeddings."""
        if not text:
            return []
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks if chunks else [text]
    
    def extract_doctor_comments(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract doctor comments with detailed metadata from thread page.
        
        Note: Agnos Health loads doctor comments dynamically via API calls,
        so this HTML parsing method has limited effectiveness.
        Use process_api_forum_data() for better results with JSON API data.
        """
        doctor_comments = []
        
        try:
            # Check meta tags first (sometimes doctor info is in meta)
            doctor_meta = soup.select_one('meta[name="author"]')
            if doctor_meta and doctor_meta.get('content'):
                author = doctor_meta.get('content', '')
                if any(prefix in author for prefix in ['นพ.', 'นพญ.', 'Dr.', 'แพทย์']):
                    print(f"    ℹ️ Found doctor in meta: {author}")
            
            # Look for any text containing doctor indicators
            all_text = soup.get_text()
            doctor_patterns = re.findall(r'(นพ\.|นพญ\.|Dr\.|แพทย์)[^\n]*', all_text)
            
            if doctor_patterns:
                print(f"    ℹ️ Found {len(doctor_patterns)} potential doctor mentions in HTML")
                for pattern in doctor_patterns[:3]:  # Show first 3
                    print(f"      • {pattern[:100]}...")
            
            # Try to find structured comment sections
            # Based on modern web apps, comments are usually in div containers
            potential_sections = soup.select("div[class*='comment'], div[class*='answer'], div[class*='reply'], div[class*='response']")
            
            if not potential_sections:
                # Try broader selectors
                potential_sections = soup.select("div p, article p, section p")
            
            for i, section in enumerate(potential_sections):
                section_text = self.clean_text(section.get_text())
                
                # Much stricter doctor detection - only medical professional responses
                is_doctor_response = False
                
                # Check for doctor title at the start
                doctor_title_at_start = re.match(r'^(นพ\.|นพญ\.|Dr\.)', section_text.strip())
                
                # Check for professional medical advice patterns (not patient questions)
                medical_advice_patterns = [
                    r'หมอแนะนำ',
                    r'การรักษาหลักจะเป็น',
                    r'โดยปกติแล้วอาการ',
                    r'จากอาการและประวัติที่แจ้ง',
                    r'อาการของคนไข้',
                    r'ลักษณะ.*ที่คนไข้แจ้ง',
                    r'น่าจะเกิดจาก',
                    r'แนะนำให้ไป.*แพทย์'
                ]
                
                has_medical_advice = any(re.search(pattern, section_text) for pattern in medical_advice_patterns)
                
                # Patient question indicators that should be excluded
                patient_indicators = [
                    r'ผมมีอาการ',
                    r'อยากจะปรึกษา',
                    r'อยากปรึกษา',
                    r'กลัวว่าจะเป็น',
                    r'เลยอยากถาม',
                    r'ควรรักษายังไง',
                    r'หลังจากผมช่วยตัวเอง',
                    r'ผมเหมือนจะเป็น',
                    r'รักษาตอนนี้ทันไหม'
                ]
                
                has_patient_indicators = any(re.search(pattern, section_text) for pattern in patient_indicators)
                
                # Only consider as doctor response if:
                # 1. Has doctor title at start OR has clear medical advice pattern
                # 2. Does NOT have patient question indicators
                # 3. Is not asking questions (ends with ?)
                ends_with_question = section_text.strip().endswith(('?', 'ครับ?', 'ค่ะ?', 'ไหม', 'ไหมครับ', 'ไหมค่ะ'))
                
                if (doctor_title_at_start or has_medical_advice) and not has_patient_indicators and not ends_with_question:
                    is_doctor_response = True
                
                if is_doctor_response:
                    # Try to extract doctor information from the text
                    doctor_match = re.search(r'(นพ\.|นพญ\.|Dr\.)\s*([^\s]+)\s+([^\s]+)', section_text)
                    
                    if doctor_match:
                        prefix = doctor_match.group(1)
                        firstname = doctor_match.group(2) or ''
                        lastname = doctor_match.group(3) or ''
                    else:
                        # Default values if we can't extract specific doctor info
                        prefix = 'นพ.'
                        firstname = 'แพทย์'
                        lastname = 'ผู้เชี่ยวชาญ'
                    
                    # Extract meaningful content (skip very short texts)
                    if len(section_text.strip()) > 50:
                        doctor_comments.append(section_text)
                        print(f"    ✅ Extracted HTML doctor comment from {prefix} {firstname} {lastname}")
                
                # Skip patient questions
                elif has_patient_indicators or ends_with_question:
                    print(f"    ⏭️ Skipped patient question/comment")
                    continue
            
            if not doctor_comments:
                print(f"    ⚠️ No doctor comments found in HTML - they may be loaded dynamically")
                print(f"    💡 Try using API data instead with process_api_forum_data()")
        
        except Exception as e:
            print(f"    ⚠️ Error extracting doctor comments: {e}")
        
        return doctor_comments
    
    def scrape_forum_list(self) -> List[Dict[str, Any]]:
        """Scrape the search page to get all thread information with pagination."""
        all_threads = []
        seen_thread_ids = set()  # Track seen thread IDs to detect duplicates
        current_page = 1
        max_pages = 10  # Allow more pages
        consecutive_empty_pages = 0
        
        while len(all_threads) < self.max_threads and current_page <= max_pages:
            # Use search page with pagination
            if current_page == 1:
                page_url = urljoin(self.base_url, "/forums/search")
            else:
                page_url = urljoin(self.base_url, f"/forums/search?page={current_page}")
            
            print(f"\n📋 Scraping forum search page {current_page}: {page_url}")
            
            try:
                resp = requests.get(page_url, headers=self.headers, timeout=30)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Find all articles on the page
                articles = soup.select("article")
                
                if not articles:
                    print(f"  ℹ️ No more threads found on page {current_page}")
                    break
                
                page_thread_count = 0
                for article in articles:
                    if len(all_threads) >= self.max_threads:
                        break
                        
                    parent_link = article.find_parent("a")
                    if parent_link and parent_link.get("href"):
                        thread_url = urljoin(self.base_url, parent_link.get("href"))
                        
                        thread_info = {}
                        
                        # Extract gender and age
                        gender_age = article.select_one("p.text-sm.text-gray-500")
                        if gender_age:
                            thread_info["gender_age"] = self.clean_text(gender_age.text)
                        
                        # Extract title (medical condition)
                        title_elem = article.select_one("p.font-bold")
                        if title_elem:
                            thread_info["title"] = self.clean_text(title_elem.text)
                        
                        # Extract date
                        date_elem = article.select_one("time span")
                        if date_elem:
                            thread_info["date_str"] = self.clean_text(date_elem.text)
                            thread_info["date"] = self.parse_thai_date(thread_info["date_str"])
                        
                        # Extract symptoms/tags
                        tags = article.select("ul li")
                        thread_info["tags"] = [
                            self.clean_text(tag.text) 
                            for tag in tags 
                            if tag.text and not tag.text.startswith('+')
                        ]
                        
                        # Extract content preview
                        content_elem = article.select_one("p.text-sm.text-gray-500.line-clamp-3")
                        if content_elem:
                            thread_info["content_preview"] = self.clean_text(content_elem.text)
                        
                        # Extract likes count
                        likes_elem = article.select_one("img[alt='thumbs-up'] + p")
                        if likes_elem:
                            thread_info["likes"] = self.clean_text(likes_elem.text)
                        
                        thread_info["url"] = thread_url
                        thread_info["thread_id"] = unquote(thread_url.split('/')[-1])
                        
                        # Skip if we've seen this thread before (duplicate across pages)
                        if thread_info["thread_id"] not in seen_thread_ids:
                            all_threads.append(thread_info)
                            seen_thread_ids.add(thread_info["thread_id"])
                            page_thread_count += 1
                
                print(f"  ✅ Found {page_thread_count} threads on page {current_page}")
                
                # Track consecutive empty pages
                if page_thread_count == 0:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 2:
                        print(f"  ℹ️ No more threads found after checking {consecutive_empty_pages} pages")
                        break
                else:
                    consecutive_empty_pages = 0
                
                # Check if we should continue to next page
                if len(all_threads) >= self.max_threads:
                    print(f"  ✅ Reached target number of threads")
                    break
                elif current_page >= max_pages:
                    print(f"  ℹ️ Reached maximum page limit ({max_pages})")
                    break
                elif consecutive_empty_pages >= 2:
                    # Already handled above, but double-check
                    break
                else:
                    # Continue to next page
                    current_page += 1
                    time.sleep(self.delay)  # Respectful delay between pages
                
            except Exception as e:
                print(f"❌ Error scraping forum list page {current_page}: {e}")
                break
        
        print(f"\n✅ Total threads found: {len(all_threads)}")
        
        return all_threads[:self.max_threads]  # Ensure we don't exceed max_threads
    
    def try_api_endpoint(self, thread_url: str) -> Optional[Dict[str, Any]]:
        """Try to fetch data from API endpoint if available."""
        try:
            # Extract thread ID from URL
            thread_id = thread_url.split('/')[-1]
            # Try common API endpoint patterns
            api_endpoints = [
                f"https://api.agnoshealth.com/forums/{thread_id}",
                f"https://app.api.agnoshealth.com/forums/{thread_id}",
                f"{self.base_url}/api/forums/{thread_id}"
            ]
            
            for api_url in api_endpoints:
                try:
                    resp = requests.get(api_url, headers=self.headers, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'forums' in data or 'forum' in data:
                            return data
                except:
                    continue
            return None
        except:
            return None
    
    def process_api_forum_data(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process API forum data into our format."""
        posts_data = []
        
        try:
            # Handle different API response structures
            forums_list = []
            if 'forums' in api_data:
                forums_list = api_data['forums']
            elif 'forum' in api_data:
                forums_list = [{'forum': api_data['forum'], 'doctor_comments': api_data.get('doctor_comments', [])}]
            
            for forum_item in forums_list:
                forum = forum_item.get('forum', {})
                doctor_comments = forum_item.get('doctor_comments', [])
                
                # Extract forum data
                forum_id = forum.get('id')
                content_text = forum.get('content_text', '')
                disease_text = forum.get('disease_text', '')
                
                
                # Process tags
                tags = []
                for tag in forum.get('default_tags', []) + forum.get('custom_tags', []):
                    tags.append(tag.get('name', ''))
                
                # Create gender_age string
                gender = "หญิง" if forum.get('user_gender') == 'female' else "ชาย" if forum.get('user_gender') == 'male' else ""
                age = forum.get('user_age', '')
                gender_age = f"{gender} อายุ {age} ปี" if gender and age else ""
                
                # Keep full doctor_comments structure with all metadata
                full_doctor_comments = []
                for comment in doctor_comments:
                    doctor_content_text = comment.get('content_text', '').strip()
                    if doctor_content_text and len(doctor_content_text) > 10:  # Only meaningful content
                        full_doctor_comments.append({
                            "id": comment.get('id'),
                            "pub_date": comment.get('pub_date'),
                            "edit_date": comment.get('edit_date'),
                            "user": {
                                "user_id": comment.get('user', {}).get('user_id'),
                                "prefix_name": comment.get('user', {}).get('prefix_name', ''),
                                "firstname": comment.get('user', {}).get('firstname', ''),
                                "lastname": comment.get('user', {}).get('lastname', ''),
                                "profile_image_url": comment.get('user', {}).get('profile_image_url', '')
                            },
                            "content_text": doctor_content_text,
                            "is_owner": comment.get('is_owner', False),
                            "is_liked": comment.get('is_liked', False),
                            "sum_likes": comment.get('sum_likes', 0)
                        })
                
                # Create post data using the patient's question from forum.content_text
                for chunk in self.chunk_text(content_text):
                    post_data = {
                        "thread_id": str(forum_id),
                        "title": disease_text,
                        "gender_age": gender_age,
                        "date": forum.get('pub_date', ''),
                        "tags": tags,
                        "content": chunk,
                        "content_type": "question",
                        "likes": str(forum.get('sum_likes', 0)),
                        "url": f"{self.base_url}/forums/{forum_id}",
                        "doctor_comments": full_doctor_comments,  # Full metadata structure
                        "scraped_at": datetime.now().isoformat()
                    }
                    posts_data.append(post_data)
        
        except Exception as e:
            print(f"    ⚠️ Error processing API data: {e}")
        
        return posts_data
    
    def scrape_thread_detail(self, thread_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape detailed content from a specific thread including doctor comments."""
        thread_url = thread_info["url"]
        print(f"  📖 Scraping: {thread_info.get('title', thread_url)[:50]}...")
        
        # Try API endpoint first
        api_data = self.try_api_endpoint(thread_url)
        if api_data:
            print(f"    ✅ Found API data")
            return self.process_api_forum_data(api_data)
        
        # Fallback to HTML scraping
        try:
            time.sleep(self.delay)  # Respectful delay
            resp = requests.get(thread_url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            posts_data = []
            
            # Extract main content
            main_content = soup.select_one("main")
            if main_content:
                question_content = main_content.select_one(".prose, .content, p.text-gray-700")
                if question_content:
                    full_content = self.clean_text(question_content.text)
                else:
                    full_content = thread_info.get("content_preview", "")
                
                # Extract doctor comments with detailed information
                doctor_comments = self.extract_doctor_comments(soup)
                
                # Create post data for question
                for chunk in self.chunk_text(full_content):
                    post_data = {
                        "thread_id": thread_info.get("thread_id"),
                        "title": thread_info.get("title", ""),
                        "gender_age": thread_info.get("gender_age", ""),
                        "date": thread_info["date"].isoformat() if thread_info.get("date") else thread_info.get("date_str"),
                        "tags": thread_info.get("tags", []),
                        "content": chunk,
                        "content_type": "question",
                        "likes": thread_info.get("likes", "0"),
                        "url": thread_url,
                        "doctor_comments": doctor_comments,
                        "scraped_at": datetime.now().isoformat()
                    }
                    posts_data.append(post_data)
            
            # Fallback to preview if no detailed content
            if not posts_data:
                for chunk in self.chunk_text(thread_info.get("content_preview", "")):
                    posts_data.append({
                        "thread_id": thread_info.get("thread_id"),
                        "title": thread_info.get("title", ""),
                        "gender_age": thread_info.get("gender_age", ""),
                        "date": thread_info["date"].isoformat() if thread_info.get("date") else thread_info.get("date_str"),
                        "tags": thread_info.get("tags", []),
                        "content": chunk,
                        "content_type": "question_preview",
                        "likes": thread_info.get("likes", "0"),
                        "url": thread_url,
                        "doctor_comments": [],
                        "scraped_at": datetime.now().isoformat()
                    })
            
            return posts_data
            
        except Exception as e:
            print(f"    ⚠️ Error: {e}")
            # Return preview data on error
            return [{
                "thread_id": thread_info.get("thread_id"),
                "title": thread_info.get("title", ""),
                "gender_age": thread_info.get("gender_age", ""),
                "date": thread_info["date"].isoformat() if thread_info.get("date") else thread_info.get("date_str"),
                "tags": thread_info.get("tags", []),
                "content": thread_info.get("content_preview", ""),
                "content_type": "question_preview",
                "likes": thread_info.get("likes", "0"),
                "url": thread_url,
                "doctor_comments": [],
                "error": str(e),
                "scraped_at": datetime.now().isoformat()
            }]
    
    def save_data(self, data: List[Dict[str, Any]], mode: str = 'w') -> None:
        """
        Save scraped data to file.
        
        Args:
            data: List of data dictionaries to save
            mode: File write mode ('w' for overwrite, 'a' for append)
        """
        new_records = 0
        duplicates = 0
        
        with open(self.output_file, mode, encoding='utf-8') as f:
            for entry in data:
                # Check for duplicates
                content_hash = self.generate_content_hash(entry)
                if content_hash in self.existing_data:
                    duplicates += 1
                    continue
                
                # Convert tags list to JSON string
                if "tags" in entry and isinstance(entry["tags"], list):
                    entry["tags"] = json.dumps(entry["tags"], ensure_ascii=False)
                
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                new_records += 1
                self.existing_data[content_hash] = entry
        
        print(f"💾 Saved {new_records} new records ({duplicates} duplicates skipped)")
    
    def aggregate_data(self) -> Dict[str, Any]:
        """Aggregate and analyze the scraped data."""
        print("\n📊 Generating aggregation statistics...")
        
        aggregations = {
            "total_records": 0,
            "unique_threads": set(),
            "conditions": defaultdict(int),
            "symptoms": defaultdict(int),
            "gender_distribution": defaultdict(int),
            "age_distribution": defaultdict(list),
            "posts_with_doctor_answers": 0,
            "date_range": {"earliest": None, "latest": None},
            "top_liked_posts": []
        }
        
        # Load and process all data
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        aggregations["total_records"] += 1
                        aggregations["unique_threads"].add(data.get("thread_id"))
                        
                        # Count conditions
                        if data.get("thread_title"):
                            # Extract condition name from title
                            match = re.search(r'\((.*?)\)', data["thread_title"])
                            if match:
                                condition = match.group(1)
                                aggregations["conditions"][condition] += 1
                        
                        # Count symptoms
                        if data.get("tags"):
                            tags = json.loads(data["tags"]) if isinstance(data["tags"], str) else data["tags"]
                            for tag in tags:
                                aggregations["symptoms"][tag] += 1
                        
                        # Gender distribution
                        if data.get("gender_age"):
                            if "หญิง" in data["gender_age"]:
                                aggregations["gender_distribution"]["female"] += 1
                            elif "ชาย" in data["gender_age"]:
                                aggregations["gender_distribution"]["male"] += 1
                            
                            # Age extraction
                            age_match = re.search(r'อายุ\s*(\d+)', data["gender_age"])
                            if age_match:
                                age = int(age_match.group(1))
                                aggregations["age_distribution"]["ages"].append(age)
                        
                        # Doctor answers
                        if data.get("has_doctor_answer"):
                            aggregations["posts_with_doctor_answers"] += 1
                        
                        # Date range
                        if data.get("date"):
                            try:
                                date_obj = datetime.fromisoformat(data["date"].replace('T', ' '))
                                if not aggregations["date_range"]["earliest"] or date_obj < aggregations["date_range"]["earliest"]:
                                    aggregations["date_range"]["earliest"] = date_obj
                                if not aggregations["date_range"]["latest"] or date_obj > aggregations["date_range"]["latest"]:
                                    aggregations["date_range"]["latest"] = date_obj
                            except:
                                pass
                        
                        # Track likes
                        likes = int(data.get("likes", "0"))
                        aggregations["top_liked_posts"].append({
                            "title": data.get("thread_title"),
                            "likes": likes,
                            "url": data.get("source_url")
                        })
                        
                    except json.JSONDecodeError:
                        continue
        
        # Process aggregations
        aggregations["unique_threads"] = len(aggregations["unique_threads"])
        
        # Calculate age statistics
        if aggregations["age_distribution"]:
            ages = aggregations["age_distribution"]["ages"]
            aggregations["age_distribution"] = {
                "min": min(ages),
                "max": max(ages),
                "average": sum(ages) / len(ages),
                "count": len(ages)
            }
        
        # Sort top symptoms and conditions
        aggregations["top_symptoms"] = dict(sorted(
            aggregations["symptoms"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        aggregations["top_conditions"] = dict(sorted(
            aggregations["conditions"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        # Get top liked posts
        aggregations["top_liked_posts"] = sorted(
            aggregations["top_liked_posts"], 
            key=lambda x: x["likes"], 
            reverse=True
        )[:5]
        
        # Format date range
        if aggregations["date_range"]["earliest"]:
            aggregations["date_range"]["earliest"] = aggregations["date_range"]["earliest"].strftime("%Y-%m-%d")
        if aggregations["date_range"]["latest"]:
            aggregations["date_range"]["latest"] = aggregations["date_range"]["latest"].strftime("%Y-%m-%d")
        
        # Clean up
        del aggregations["symptoms"]
        del aggregations["conditions"]
        
        return aggregations
    
    def print_stats(self, stats: Dict[str, Any]) -> None:
        """Print aggregation statistics in a formatted way."""
        print("\n" + "="*60)
        print("📈 AGGREGATION STATISTICS")
        print("="*60)
        
        print(f"\n📁 Total Records: {stats['total_records']}")
        print(f"🔖 Unique Threads: {stats['unique_threads']}")
        print(f"👨‍⚕️ Posts with Doctor Answers: {stats['posts_with_doctor_answers']}")
        
        print(f"\n📅 Date Range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        
        print("\n👥 Gender Distribution:")
        for gender, count in stats['gender_distribution'].items():
            print(f"  - {gender.capitalize()}: {count}")
        
        if stats.get('age_distribution'):
            print(f"\n🎂 Age Statistics:")
            print(f"  - Average: {stats['age_distribution']['average']:.1f} years")
            print(f"  - Range: {stats['age_distribution']['min']}-{stats['age_distribution']['max']} years")
        
        print("\n🏥 Top Medical Conditions:")
        for condition, count in list(stats['top_conditions'].items())[:5]:
            print(f"  - {condition}: {count} mentions")
        
        print("\n💊 Top Symptoms:")
        for symptom, count in list(stats['top_symptoms'].items())[:5]:
            print(f"  - {symptom}: {count} mentions")
        
        print("\n👍 Most Liked Posts:")
        for post in stats['top_liked_posts']:
            if post['title']:
                print(f"  - {post['title'][:50]}... ({post['likes']} likes)")
        
        print("\n" + "="*60)
    
    def run(self, mode: str = 'full', aggregate_only: bool = False) -> None:
        """
        Run the scraper.
        
        Args:
            mode: 'full' for complete scrape, 'update' for incremental
            aggregate_only: If True, only run aggregation on existing data
        """
        if aggregate_only:
            stats = self.aggregate_data()
            self.print_stats(stats)
            
            # Save aggregation to file
            with open('aggregation_stats.json', 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"\n📊 Aggregation saved to aggregation_stats.json")
            return
        
        print(f"\n🚀 Starting Agnos Health Forum Scraper")
        print(f"Mode: {mode.upper()}")
        print(f"Max threads: {self.max_threads}")
        print(f"Output file: {self.output_file}")
        print("-" * 60)
        
        # Load existing data if in update mode
        if mode == 'update':
            self.load_existing_data()
        
        # Scrape forum list
        threads = self.scrape_forum_list()
        
        if not threads:
            print("❌ No threads found. Please check the website structure.")
            return
        
        # Filter for new threads only in update mode
        if mode == 'update':
            original_count = len(threads)
            threads = self.get_new_threads_only(threads)
            new_count = len(threads)
            skipped_count = original_count - new_count
            
            print(f"\n🔄 Update Mode Summary:")
            print(f"  📋 Total threads found: {original_count}")
            print(f"  ⏭️ Already scraped: {skipped_count}")
            print(f"  🆕 New threads to scrape: {new_count}")
            
            if new_count == 0:
                print("✅ No new threads to scrape. All threads are up to date!")
                return
        
        # Scrape each thread
        all_data = []
        for i, thread in enumerate(threads, 1):
            print(f"\n📄 Processing thread {i}/{len(threads)}")
            
            thread_data = self.scrape_thread_detail(thread)
            all_data.extend(thread_data)
        
        # Save data
        if all_data:
            save_mode = 'a' if mode == 'update' else 'w'
            self.save_data(all_data, mode=save_mode)
        
        # Print summary
        print("\n" + "="*60)
        print("✅ SCRAPING COMPLETE!")
        print(f"📋 Threads processed: {len(threads)}")
        print(f"💾 Data chunks saved: {len(all_data)}")
        print(f"📁 Output file: {self.output_file}")
        
        # Run aggregation
        stats = self.aggregate_data()
        self.print_stats(stats)


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Agnos Health Forum Scraper - Extract and analyze medical forum data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full scrape (default)
  python agnos_forum_scraper.py
  
  # Update mode (append new data only)
  python agnos_forum_scraper.py --mode update
  
  # Scrape specific number of threads
  python agnos_forum_scraper.py --max-threads 50
  
  # Only run aggregation on existing data
  python agnos_forum_scraper.py --aggregate-only
  
  # Custom output file
  python agnos_forum_scraper.py --output my_data.jsonl
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'update'],
        default='full',
        help='Scraping mode: full (overwrite) or update (append new)'
    )
    
    parser.add_argument(
        '--max-threads',
        type=int,
        default=50,
        help='Maximum number of threads to scrape (default: 50)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--output',
        default='forum_data.jsonl',
        help='Output filename (default: forum_data.jsonl)'
    )
    
    parser.add_argument(
        '--aggregate-only',
        action='store_true',
        help='Only run aggregation on existing data without scraping'
    )
    
    args = parser.parse_args()
    
    # Initialize and run scraper
    scraper = AgnosForumScraper(
        max_threads=args.max_threads,
        delay=args.delay,
        output_file=args.output
    )
    
    try:
        scraper.run(
            mode=args.mode,
            aggregate_only=args.aggregate_only
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()