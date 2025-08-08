#!/usr/bin/env python3
"""
Data Management Page for Agnos Health Chatbot
Handles forum data analytics, visualization, and updates
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys
from datetime import datetime
from collections import Counter
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the scraper
try:
    from src.scraper import AgnosForumScraper
except ImportError as e:
    st.error(f"❌ Could not import AgnosForumScraper: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="Data Management - Agnos Health",
    page_icon="📊",
    layout="wide"
)

def load_forum_data():
    """Load forum data from JSONL file"""
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'forum_data.jsonl')
    data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            st.error(f"Error loading data: {e}")
    return data

def analyze_forum_data(data):
    """Analyze forum data for statistics"""
    if not data:
        return None
    
    # Basic statistics
    total_threads = len(data)
    
    # Extract diseases
    diseases = []
    tags_all = []
    dates = []
    doctor_comment_counts = []
    
    for item in data:
        # Extract disease from title
        title = item.get('title', '')
        if title:
            diseases.append(title)
        
        # Extract tags
        tags = item.get('tags', '')
        if isinstance(tags, str):
            try:
                tag_list = json.loads(tags)
                tags_all.extend(tag_list)
            except:
                tags_all.append(tags)
        elif isinstance(tags, list):
            tags_all.extend(tags)
        
        # Extract dates
        date = item.get('date', '')
        if date:
            dates.append(date)
        
        # Count doctor comments
        doctor_comments = item.get('doctor_comments', [])
        doctor_comment_counts.append(len(doctor_comments))
    
    # Disease distribution
    disease_counts = Counter(diseases)
    
    # Tag distribution
    tag_counts = Counter(tags_all)
    
    # Threads with doctor responses
    threads_with_doctor = sum(1 for count in doctor_comment_counts if count > 0)
    
    return {
        'total_threads': total_threads,
        'disease_counts': disease_counts,
        'tag_counts': tag_counts,
        'dates': dates,
        'threads_with_doctor': threads_with_doctor,
        'doctor_comment_counts': doctor_comment_counts,
        'unique_diseases': len(disease_counts),
        'unique_tags': len(tag_counts)
    }

def create_disease_bar_chart(disease_counts, top_n=15):
    """Create bar chart for disease distribution"""
    # Get top N diseases
    top_diseases = dict(disease_counts.most_common(top_n))
    
    # Create dataframe
    df = pd.DataFrame(list(top_diseases.items()), columns=['Disease', 'Count'])
    
    # Create bar chart with single color
    fig = px.bar(
        df, 
        x='Count', 
        y='Disease',
        orientation='h',
        title=f'Top {top_n} Diseases/Conditions in Forum',
        labels={'Count': 'Number of Threads', 'Disease': 'Disease/Condition'}
    )
    
    # Update bar color to match theme
    fig.update_traces(marker_color='#0066cc')
    
    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_tag_pie_chart(tag_counts, top_n=10):
    """Create pie chart for tag distribution"""
    # Get top N tags
    top_tags = dict(tag_counts.most_common(top_n))
    
    # Add "Others" category
    total_tags = sum(tag_counts.values())
    top_tags_sum = sum(top_tags.values())
    if total_tags > top_tags_sum:
        top_tags['Others'] = total_tags - top_tags_sum
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=list(top_tags.keys()),
        values=list(top_tags.values()),
        hole=0.3
    )])
    
    fig.update_layout(
        title=f'Top {top_n} Tags Distribution',
        height=500
    )
    
    return fig

def create_timeline_chart(dates):
    """Create timeline chart for forum posts"""
    if not dates:
        return None
    
    # Parse dates
    parsed_dates = []
    for date_str in dates:
        try:
            if 'T' in date_str:
                date_obj = datetime.fromisoformat(date_str.split('T')[0])
            else:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            parsed_dates.append(date_obj)
        except:
            continue
    
    if not parsed_dates:
        return None
    
    # Create dataframe
    df = pd.DataFrame({'date': parsed_dates})
    df['count'] = 1
    
    # Group by month
    df['month'] = df['date'].dt.to_period('M')
    monthly_counts = df.groupby('month')['count'].sum().reset_index()
    monthly_counts['month'] = monthly_counts['month'].dt.to_timestamp()
    
    # Create line chart
    fig = px.line(
        monthly_counts,
        x='month',
        y='count',
        title='Forum Activity Over Time',
        labels={'month': 'Month', 'count': 'Number of Threads'}
    )
    
    fig.update_layout(height=400)
    
    return fig

def update_forum_data():
    """Update forum data using the scraper"""
    try:
        # Initialize scraper
        scraper = AgnosForumScraper(
            base_url="https://www.agnoshealth.com/forums",
            output_file=data_file
        )
        
        # Run update mode
        scraper.run(mode='update')
        
        return True, "Data updated successfully!"
    except Exception as e:
        return False, f"Error updating data: {str(e)}"

def main():
    """Main function for data management page"""
    
    # Header
    st.title("📊 Forum Data Management")
    st.markdown("Analyze and manage Agnos Health forum data")
    
    # Load data
    data = load_forum_data()
    
    if not data:
        st.warning("No forum data found. Please run the scraper first.")
        if st.button("🔄 Scrape Initial Data"):
            with st.spinner("Scraping forum data... This may take a few minutes."):
                success, message = update_forum_data()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        return
    
    # Analyze data
    stats = analyze_forum_data(data)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Visualizations", "📋 Dataset", "🔄 Update Data"])
    
    with tab1:
        st.header("📈 Data Overview")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Threads",
                value=f"{stats['total_threads']:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Unique Diseases",
                value=f"{stats['unique_diseases']:,}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Threads with Doctor Responses",
                value=f"{stats['threads_with_doctor']:,}",
                delta=f"{stats['threads_with_doctor']/stats['total_threads']*100:.1f}%"
            )
        
        with col4:
            st.metric(
                label="Unique Tags",
                value=f"{stats['unique_tags']:,}",
                delta=None
            )
        
        # Summary statistics
        st.subheader("📊 Summary Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top 5 Diseases/Conditions:**")
            for i, (disease, count) in enumerate(stats['disease_counts'].most_common(5), 1):
                st.write(f"{i}. {disease} ({count} threads)")
        
        with col2:
            st.write("**Top 5 Tags:**")
            for i, (tag, count) in enumerate(stats['tag_counts'].most_common(5), 1):
                st.write(f"{i}. {tag} ({count} occurrences)")
        
        # Data quality
        st.subheader("📋 Data Quality")
        
        avg_doctor_comments = sum(stats['doctor_comment_counts']) / len(stats['doctor_comment_counts'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Average Doctor Comments per Thread",
                f"{avg_doctor_comments:.2f}"
            )
        
        with col2:
            st.metric(
                "Response Rate",
                f"{stats['threads_with_doctor']/stats['total_threads']*100:.1f}%"
            )
        
        with col3:
            st.metric(
                "Total Doctor Comments",
                f"{sum(stats['doctor_comment_counts']):,}"
            )
    
    with tab2:
        st.header("📊 Data Visualizations")
        
        # Disease distribution bar chart
        st.subheader("Disease/Condition Distribution")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            top_n_diseases = st.slider("Number of diseases to show", 5, 30, 15)
        
        disease_chart = create_disease_bar_chart(stats['disease_counts'], top_n_diseases)
        st.plotly_chart(disease_chart, use_container_width=True)
        
        # Tag distribution pie chart
        st.subheader("Tag Distribution")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            top_n_tags = st.slider("Number of tags to show", 5, 20, 10)
        
        tag_chart = create_tag_pie_chart(stats['tag_counts'], top_n_tags)
        st.plotly_chart(tag_chart, use_container_width=True)
        
        # Timeline chart
        if stats['dates']:
            st.subheader("Forum Activity Timeline")
            timeline_chart = create_timeline_chart(stats['dates'])
            if timeline_chart:
                st.plotly_chart(timeline_chart, use_container_width=True)
    
    with tab3:
        st.header("📋 Dataset Details")
        
        # Convert to dataframe for display
        df = pd.DataFrame(data)
        
        # Data preview
        st.subheader("Data Preview")
        
        # Search and filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search in titles", "")
        
        with col2:
            filter_disease = st.selectbox(
                "Filter by disease",
                ["All"] + list(stats['disease_counts'].keys())[:20]
            )
        
        with col3:
            filter_doctor = st.selectbox(
                "Filter by doctor response",
                ["All", "With Doctor Response", "Without Doctor Response"]
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
        
        if filter_disease != "All":
            filtered_df = filtered_df[filtered_df['title'] == filter_disease]
        
        if filter_doctor == "With Doctor Response":
            filtered_df = filtered_df[filtered_df['doctor_comments'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
        elif filter_doctor == "Without Doctor Response":
            filtered_df = filtered_df[filtered_df['doctor_comments'].apply(lambda x: len(x) == 0 if isinstance(x, list) else True)]
        
        # Display filtered data
        st.write(f"Showing {len(filtered_df)} of {len(df)} threads")
        
        # Select columns to display
        display_columns = ['thread_id', 'title', 'date', 'gender_age', 'tags', 'url']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # Add doctor comment count
        if 'doctor_comments' in filtered_df.columns:
            filtered_df['doctor_count'] = filtered_df['doctor_comments'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            available_columns.append('doctor_count')
        
        # Display dataframe
        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True,
            height=500
        )
        
        # Download options
        st.subheader("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export as CSV
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"forum_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export as JSON
            json_str = filtered_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_str,
                file_name=f"forum_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with tab4:
        st.header("🔄 Update Forum Data")
        
        st.info("""
        **Update Modes:**
        - **Update**: Fetch only new threads not in the database
        - **Full Refresh**: Re-scrape all threads (takes longer)
        """)
        
        # Current data info
        st.subheader("Current Data Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Threads", f"{stats['total_threads']:,}")
        
        with col2:
            # Get latest date
            if stats['dates']:
                latest_date = max(stats['dates'])
                st.metric("Latest Thread Date", latest_date[:10] if latest_date else "N/A")
            else:
                st.metric("Latest Thread Date", "N/A")
        
        with col3:
            # File size
            data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'forum_data.jsonl')
            file_size = os.path.getsize(data_file) / (1024 * 1024)  # MB
            st.metric("Database Size", f"{file_size:.2f} MB")
        
        # Update controls
        st.subheader("Update Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            update_mode = st.radio(
                "Select update mode:",
                ["Update (New threads only)", "Full Refresh (All threads)"]
            )
        
        with col2:
            max_threads = st.number_input(
                "Maximum threads to scrape:",
                min_value=5,
                max_value=100,
                value=20,
                help="Number of threads to scrape"
            )
        
        # Update button
        if st.button("🚀 Start Update", type="primary"):
            with st.spinner(f"Updating forum data... This may take a few minutes."):
                try:
                    # Determine mode
                    mode = 'update' if 'Update' in update_mode else 'full'
                    
                    # Run scraper
                    scraper = AgnosForumScraper(
                        base_url="https://www.agnoshealth.com/forums",
                        output_file=data_file,
                        max_threads=max_threads
                    )
                    
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Run scrape
                    status_text.text(f"Starting {mode} scrape...")
                    scraper.run(mode=mode)
                    
                    progress_bar.progress(100)
                    status_text.text("Update completed!")
                    
                    st.success(f"✅ Successfully updated forum data in {mode} mode!")
                    
                    # Show update stats
                    new_data = load_forum_data()
                    new_threads = len(new_data) - stats['total_threads']
                    
                    if new_threads > 0:
                        st.info(f"📈 Added {new_threads} new threads to the database")
                    else:
                        st.info("📊 No new threads found")
                    
                    # Refresh button
                    if st.button("🔄 Refresh Page"):
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error updating data: {str(e)}")
                    st.error("Please check your internet connection and try again.")
        
        # Manual update instructions
        with st.expander("🛠️ Manual Update Instructions"):
            st.code("""
# Run update from command line:
python agnos_forum_scraper.py --mode update

# Full refresh:
python agnos_forum_scraper.py --mode full

# Specify pages:
python agnos_forum_scraper.py --mode update --pages 10
            """, language="bash")
        
        # Backup options
        st.subheader("💾 Backup Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📦 Create Backup"):
                try:
                    import shutil
                    backup_name = f"forum_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
                    data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'forum_data.jsonl')
                    backup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', backup_name)
                    shutil.copy(data_file, backup_path)
                    st.success(f"✅ Backup created: {backup_name}")
                except Exception as e:
                    st.error(f"❌ Backup failed: {str(e)}")
        
        with col2:
            # List existing backups
            import glob
            backups = glob.glob('../forum_data_backup_*.jsonl')
            if backups:
                selected_backup = st.selectbox("Restore from backup:", backups)
                if st.button("♻️ Restore Backup"):
                    try:
                        import shutil
                        data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'forum_data.jsonl')
                        shutil.copy(selected_backup, data_file)
                        st.success(f"✅ Restored from: {selected_backup}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Restore failed: {str(e)}")

if __name__ == "__main__":
    main()