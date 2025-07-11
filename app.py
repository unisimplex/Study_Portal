import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pickle
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import re
from urllib.parse import urlparse, parse_qs
import base64
import time
import subprocess


# Configure page
st.set_page_config(
    page_title="Study Portal",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .logo {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    .timer-section {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .user-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .subject-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: white;
    }
    
    .video-container {
        border: 1px solid #808080;
        border-radius: 8px;
        # padding: 1rem;
        margin-bottom: 1rem;
        padding-top: 0.15rem;
        text-align: center;
    }
    
    .progress-container {
        margin-top: 1rem;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 4px;
    }
    
    .add-button {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border: 2px dashed #1f77b4;
        border-radius: 8px;
        background: none;
        color: #1f77b4;
        cursor: pointer;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .pdf-viewer {
        width: 100%;
        height: 800px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    
    .stButton > button {
        width: 100%;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# DataManager Class
class DataManager:
    def __init__(self):
        self.data_dir = "exam_prep_data"
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_user_data_path(self, username: str) -> str:
        """Get user-specific data directory"""
        user_dir = os.path.join(self.data_dir, username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        return user_dir
    
    def save_users(self, users: Dict):
        """Save users data to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def load_users(self) -> Dict:
        """Load users data from JSON file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_user_data(self, username: str, data: Dict):
        """Save user-specific data"""
        user_dir = self.get_user_data_path(username)
        data_file = os.path.join(user_dir, "user_data.json")
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_user_data(self, username: str) -> Dict:
        """Load user-specific data"""
        user_dir = self.get_user_data_path(username)
        data_file = os.path.join(user_dir, "user_data.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_user_data()
        return self.get_default_user_data()
    
    def get_default_user_data(self) -> Dict:
        """Get default user data structure"""
        return {
            "subjects": {},
            "study_sessions": [],
            "total_study_time": 0,
            "last_login": datetime.datetime.now().isoformat()
        }
    
    def save_pdf_file(self, username: str, subject: str, filename: str, file_content: bytes):
        """Save uploaded PDF file"""
        user_dir = self.get_user_data_path(username)
        pdf_dir = os.path.join(user_dir, "pdfs", subject)
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        file_path = os.path.join(pdf_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return file_path
    
    def get_pdf_files(self, username: str, subject: str) -> List[str]:
        """Get list of PDF files for a subject"""
        user_dir = self.get_user_data_path(username)
        pdf_dir = os.path.join(user_dir, "pdfs", subject)
        if os.path.exists(pdf_dir):
            return [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        return []

data_manager = DataManager()

# Useful Functions
def extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_playlist_id(url: str) -> str:
    """Extract YouTube playlist ID from URL"""
    pattern = r'list=([^&\n?#]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def format_time(seconds: int) -> str:
    """Format seconds to HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_video_embed_url(video_id: str, start_time: int = 0) -> str:
    """Get YouTube embed URL with start time"""
    return f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=0"

def display_pdf_viewer(pdf_path):
    """Returns parsed pdf data"""
    try:
        if not os.path.exists(pdf_path):
            st.error("PDF file not found")
            return False        
        pdf_name = os.path.basename(pdf_path)    
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        # Encode for embedding
        b64_pdf = base64.b64encode(pdf_data).decode()
        pdf_url = f"data:application/pdf;base64,{b64_pdf}"               
        
        return pdf_data,pdf_url
        
    except Exception as e:
        st.error(f"Could not display PDF: {e}")
        return False
    

@st.dialog("Profile Details")
def profile(username):
    username = st.session_state.username

    users = data_manager.load_users()
    user_data = data_manager.load_user_data(username)
    
    if username not in users:
        st.error("User not found!")
        return
    
    user_info = users[username]
    
    with st.container():
                last_login = user_data.get('last_login', 'Never')
                if last_login != 'Never':
                    try:
                        last_login_dt = datetime.datetime.fromisoformat(last_login)
                        formatted_date = last_login_dt.strftime("%B %d, %Y at %I:%M %p")
                    except:
                        pass
                components.html(f"""<style>.user-info{{display:flex;align-items:center;gap:15px;background:#fff;padding:20px 30px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}}.logo{{height:50px;width:50px;flex-shrink:0}}.details{{display:flex;flex-direction:column;gap:8px;font-size:18px;line-height:1.4;text-align:left}}.details .username{{font-weight:700}}.details .last-login{{font-weight:700;color:#555}}</style><div class="user-info"><svg class="logo" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" fill="#4A90E2"><circle cx="32" cy="32" r="30" stroke="#4A90E2" stroke-width="4" fill="#E1ECF7"/><circle cx="32" cy="24" r="10" fill="#4A90E2"/><path d="M16 50c0-8.837 7.163-16 16-16s16 7.163 16 16" fill="#4A90E2"/></svg><div class="details"><div class="username">Username: <strong>{username}</strong></div><div class="last-login">Last login: <strong>{formatted_date}</strong></div></div></div>""", height=130)
    
    col1, col2 = st.columns(2)    
    with col1:
        if st.button("🔑 Change ID & Password", use_container_width=True):
            st.session_state.show_change_credentials = True
            st.session_state.show_delete_confirmation = False
    
    with col2:
        if st.button("🗑️ Delete User", use_container_width=True, type="secondary"):
            st.session_state.show_delete_confirmation = True
            st.session_state.show_change_credentials = False
    
    if st.session_state.get('show_change_credentials', False):
        st.subheader("Change Credentials")        
        new_username = st.text_input("New Username", value=username)
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Changes"):
                if new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 3:
                    st.error("Password must be at least 3 characters!")
                elif new_username != username and new_username in users:
                    st.error("Username already exists!")
                else:
                    old_user_data = users[username].copy()
                    
                    if new_username != username:
                        del users[username]
                        import shutil
                        old_dir = data_manager.get_user_data_path(username)
                        new_dir = data_manager.get_user_data_path(new_username)
                        if os.path.exists(old_dir):
                            shutil.move(old_dir, new_dir)
                    
                    users[new_username] = old_user_data
                    users[new_username]['password'] = new_password
                    
                    data_manager.save_users(users)
                    
                    st.session_state.username = new_username
                    st.session_state.show_change_credentials = False
                    
                    st.success("Credentials updated successfully!")
                    st.rerun()
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.show_change_credentials = False
                st.rerun()
    
    if st.session_state.get('show_delete_confirmation', False):
        st.subheader("⚠️ Delete User")
        st.warning("This action cannot be undone! All your data will be permanently deleted.")
        
        confirm_text = st.text_input("Type 'DELETE' to confirm:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Confirm Delete", type="primary"):
                if confirm_text == "DELETE":
                    import shutil
                    user_dir = data_manager.get_user_data_path(username)
                    if os.path.exists(user_dir):
                        shutil.rmtree(user_dir)
                    
                    del users[username]
                    data_manager.save_users(users)
                    
                    st.session_state.clear()
                    st.success("User deleted successfully!")
                    st.rerun()
                else:
                    st.error("Please type 'DELETE' to confirm.")
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.show_delete_confirmation = False
                st.rerun()

@st.dialog("Are You Sure ?")
def del_sub(subject_name):
    col1 , col2 = st.columns([1,1])
    with col2:
        if st.button("👉🏻🗑️ YES", key=f"del_sub_yes_{subject_name}"):                            
                del st.session_state.user_data['subjects'][subject_name]
                data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                if 'selected_subject' in st.session_state and st.session_state.selected_subject == subject_name:
                    del st.session_state.selected_subject
                st.rerun()
    with col1:
        if st.button("❌ NO",key=f"del_sub_no_{subject_name}"):
            st.rerun()

@st.dialog("Are You Sure ?")
def del_dialog(subject,video_index,vid_obj):
    col1 , col2 = st.columns([1,1])
    with col2:
        if st.button("👉🏻🗑️ Yes ", key=f"del_dialog_yes{subject}_{video_index}"):
                        vid_obj.pop(video_index)
                        data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                        st.rerun()  
    with col1:
        if st.button("❌ NO",key=f"del_dialog_no{subject}_{video_index}"):
            st.rerun()


@st.dialog("Are You Sure ?")
def del_pdf(subject,i,pdf,subject_data):
    col1 , col2 = st.columns([1,1])
    with col2:
        if st.button("👉🏻🗑️ YES", key=f"del_pdf_yes_{subject}_{i}"):                            
                if os.path.exists(pdf['path']):
                    os.remove(pdf['path'])
                subject_data['pdfs'].pop(i)
                data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                st.rerun()
    with col1:
        if st.button("❌ NO",key=f"del_pdf_no_{subject}_{i}"):
            st.rerun()


# Authentication Functions
def login_user(username: str, password: str) -> bool:
    """Authenticate user"""
    users = data_manager.load_users()
    if username in users and users[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.user_data = data_manager.load_user_data(username)
        return True
    return False

def register_user(username: str, password: str) -> bool:
    """Register new user"""
    users = data_manager.load_users()
    if username not in users:
        users[username] = {
            'password': password,
            'created_at': datetime.datetime.now().isoformat()
        }
        data_manager.save_users(users)
        
        default_data = data_manager.get_default_user_data()
        data_manager.save_user_data(username, default_data)
        return True
    return False

# Main App Functions
def render_header():
    """Render main header"""
    col1, col2 , col3 = st.columns([0.5, 0.3,0.2])
    # print("\n" , st.session_state)
    with col1:
        if 'study_start_time' not in st.session_state:
            st.session_state.study_start_time = None
        
        timer_col1, timer_col2 = st.columns([1,1])
        with timer_col1:
            if st.button("⏰ Start Study Timer"):
                st.session_state.study_start_time = datetime.datetime.now()
                st.rerun()
        
        with timer_col2:
            if st.button("⏹️ Stop Timer"):
                if st.session_state.study_start_time:
                    study_time = (datetime.datetime.now() - st.session_state.study_start_time).total_seconds()
                    st.session_state.user_data['total_study_time'] += study_time
                    st.session_state.user_data['study_sessions'].append({
                        'date': datetime.datetime.now().isoformat(),
                        'duration': study_time
                    })
                    data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                    st.session_state.study_start_time = None
                    st.success(f"Study session saved! Duration: {format_time(int(study_time))}")
                    st.rerun()
        
        if st.session_state.study_start_time:
            elapsed = (datetime.datetime.now() - st.session_state.study_start_time).total_seconds()
            st.info(f"⏱️ Current session: {format_time(int(elapsed))}")
    
    with col2:
            if st.button("🚪 Log Out"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()        
    with col3:
            if st.button(f"👤  {st.session_state.username}",disabled = False):
                profile(st.session_state.username)
         
            
def render_sidebar():   
    """Render sidebar with subject management"""
    st.sidebar.title("📚 Subjects",width="stretch")
    
    # Add new subject
    with st.sidebar.expander("➕ Add New Subject"):
        new_subject = st.text_input("Subject Name", key="new_subject_input")
        if st.button("Add Subject", key="add_subject_btn"):
            if new_subject and new_subject not in st.session_state.user_data['subjects']:
                st.session_state.user_data['subjects'][new_subject] = {
                    'videos': [],
                    'playlists': [],
                    'pdfs': [],
                    'created_at': datetime.datetime.now().isoformat()
                }
                data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                st.success(f"Subject '{new_subject}' added!")
                st.rerun()
            elif new_subject in st.session_state.user_data['subjects']:
                st.error("Subject already exists!")
    
    subjects = st.session_state.user_data['subjects']
    if subjects:
        for subject_name in subjects.keys():
            col1, col2 = st.sidebar.columns([0.8, 0.1],gap="small")
            with col1:
                if st.button(f"📖 {subject_name}", key=f"subject_{subject_name}"):
                    st.session_state.selected_subject = subject_name
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{subject_name}"):
                    del_sub(subject_name)
    else:
        st.sidebar.info("No subjects yet. Add your first subject above!")
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Data Management")
    
    if st.sidebar.button("📤 Export Data"):
        export_data = {
            'user_data': st.session_state.user_data,
            'export_date': datetime.datetime.now().isoformat()
        }
        json_str = json.dumps(export_data, indent=2)
        st.sidebar.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"exam_prep_data_{st.session_state.username}.json",
            mime="application/json"
        )
    
    uploaded_file = st.sidebar.file_uploader("📥 Import Data", type=['json'])
    if uploaded_file:
        try:
            import_data = json.load(uploaded_file)
            if 'user_data' in import_data:
                st.session_state.user_data.update(import_data['user_data'])
                data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                st.sidebar.success("Data imported successfully!")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error importing data: {str(e)}")


def render_video_player(video_data: Dict, subject: str, video_index: int, vid_obj):
    """Render video player with progress tracking"""


    with st.container(border=True):
        video_id = video_data['id']
        title = video_data['title']
        progress = video_data.get('progress', 0)
        last_position = video_data.get('last_position', 0)
        
        col1 , col2 = st.columns([1,1])
        with col1:
            st.markdown(f"### 🎥 {title}")
        with col2:
            if st.button("🗑️", key=f"delete_video_{subject}_{video_index}"):
                del_dialog(subject,video_index,vid_obj)

        embed_url = get_video_embed_url(video_id, last_position)
        st.markdown(f"""
            <div class="video-container">
                <iframe width="100%" height="300px" src="{embed_url}" 
                        frameborder="0" allowfullscreen></iframe>
            </div>
        """, unsafe_allow_html=True)
        
        col1 , col2 , col3 = st.columns([1,1,1])
        with col1:
            hours =  st.number_input("Hours", min_value=0, key=f"time_hour_{subject}_{video_index}")
        with col2:
            minutes = st.number_input("Minutes", min_value=0, max_value=59, key=f"time_min_{subject}_{video_index}")
        with col3:
            seconds = st.number_input("Seconds", min_value=0, max_value=59, key=f"time_sec_{subject}_{video_index}")

        if st.button("💾 Save Position", key=f"save_pos_{subject}_{video_index}"):
            if hours != 0 :
                total_seconds = ((hours * 60) + minutes) * 60 + seconds
            else:
                total_seconds =  minutes * 60 + seconds

            st.session_state.user_data['subjects'][subject]['videos'][video_index]['last_position'] = total_seconds
            data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
            st.success(f"Position saved at {format_time(total_seconds)}")
            st.rerun()


def render_playlist(playlists,playlist_idx,subject):
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown(f"### 📋 {playlists[playlist_idx]['title']}")
    with col2:
        if st.button("🗑️", key=f"delete_playlist_{subject}_{playlist_idx}"):
            del_dialog(subject,playlist_idx,playlists)                                    
    
    vid_index = playlists[playlist_idx]['index']
    start_time = playlists[playlist_idx]['last_position']
    embed_url = f"https://www.youtube.com/embed/?listType=playlist&list={playlists[playlist_idx]['id']}&index={vid_index}&start={start_time}"
    # print(embed_url)
    st.markdown(f"""
        <div class="video-container">
            <iframe width="100%" height="300px" src="{embed_url}" 
                    frameborder="0" allowfullscreen></iframe>
        </div>
        
    """, unsafe_allow_html=True,)   

    col1 , col2 , col3,col4 = st.columns([1,1,1,1])
    with col1:
        Index =  st.number_input("Index", min_value=0, key=f"play_vid_index{subject}_{playlist_idx}")

    with col2:
        hours =  st.number_input("Hours", min_value=0, key=f"play_time_hour_{subject}_{playlist_idx}")
    with col3:
        minutes = st.number_input("Minutes", min_value=0, max_value=59, key=f"play_time_min_{subject}_{playlist_idx}")
    with col4:
        seconds = st.number_input("Seconds", min_value=0, max_value=59, key=f"play_time_sec_{subject}_{playlist_idx}")

    if st.button("💾 Save Position", key=f"play_save_pos_{subject}_{playlist_idx}"):
        if hours != 0 :
            total_seconds = ((hours * 60) + minutes) * 60 + seconds
        else:
            total_seconds =  minutes * 60 + seconds

        # print(st.session_state.user_data)
        st.session_state.user_data['subjects'][subject]['playlists'][playlist_idx]['index'] = Index
        st.session_state.user_data['subjects'][subject]['playlists'][playlist_idx]['last_position'] = total_seconds

        data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
        st.success(f"Position saved at {format_time(total_seconds)}")
        st.rerun()  


def render_subject_content():
    """Render content for selected subject"""
    if 'selected_subject' not in st.session_state:
        st.info("👈 Select a subject from the sidebar to get started!")
        return
    
    subject = st.session_state.selected_subject
    subject_data = st.session_state.user_data['subjects'][subject]
    
    st.header(f"📚 {subject}")

    tab1, tab2, tab3 = st.tabs(["🎥 Videos", "📋 Playlists", "📄 PDFs"])
   
    with tab1:
        st.subheader("YouTube Videos")
        
        # Add new video
        with st.expander("➕ Add New Video"):
            video_url = st.text_input("YouTube Video URL", key=f"video_url_{subject}")
            video_title = st.text_input("Video Title (optional)", key=f"video_title_{subject}")
            
            if st.button("Add Video", key=f"add_video_{subject}"):
                video_id = extract_youtube_id(video_url)
                if video_id:
                    title = video_title or f"Video {len(subject_data['videos']) + 1}"
                    new_video = {
                        'id': video_id,
                        'title': title,
                        'url': video_url,
                        'progress': 0,
                        'last_position': 0,
                        'added_at': datetime.datetime.now().isoformat()
                    }
                    subject_data['videos'].append(new_video)
                    data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                    st.success("Video added successfully!")
                    st.rerun()
                else:
                    st.error("Invalid YouTube URL")
        
        if subject_data['videos']:
            videos = subject_data['videos']          
            num_rows = (len(videos) + 2) // 3              
            for row in range(num_rows):
                cols = st.columns(3)                
                for col_idx in range(3):
                    video_idx = row * 3 + col_idx                    
                    if video_idx < len(videos):
                        with cols[col_idx]:
                            with st.container():
                                render_video_player(videos[video_idx], subject, video_idx,videos)
                             
        else:
            st.info("No videos added yet. Add your first video above!")
            
     
    with tab2:
        st.subheader("YouTube Playlists")
        
        # Add new playlist
        with st.expander("➕ Add New Playlist"):
            playlist_url = st.text_input("YouTube Playlist URL", key=f"playlist_url_{subject}")
            playlist_title = st.text_input("Playlist Title (optional)", key=f"playlist_title_{subject}")
            
            if st.button("Add Playlist", key=f"add_playlist_{subject}"):
                playlist_id = extract_playlist_id(playlist_url)
                if playlist_id:
                    title = playlist_title or f"Playlist {len(subject_data['playlists']) + 1}"
                    new_playlist = {
                        'id': playlist_id,
                        'title': title,
                        'url': playlist_url,
                        'progress': 0,
                        'last_position': 0,
                        'index': 1,
                        'added_at': datetime.datetime.now().isoformat()
                    }
                    subject_data['playlists'].append(new_playlist)
                    data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                    st.success("Playlist added successfully!")
                    st.rerun()
                else:
                    st.error("Invalid YouTube playlist URL")
        
        
        # Display playlists
        if subject_data['playlists']:
            playlists = subject_data['playlists']            
            num_rows = (len(playlists) + 2) // 3              
            for row in range(num_rows):
                cols = st.columns(3)                
                for col_idx in range(3):
                    playlist_idx = row * 3 + col_idx                    
                    if playlist_idx < len(playlists):
                        with cols[col_idx]:
                            with st.container(border=True):
                               render_playlist(playlists,playlist_idx,subject)                             
                                                
        else:
            st.info("No playlists added yet. Add your first playlist above!")
    
    with tab3:
        st.subheader("PDF Documents")
        
        uploaded_files = st.file_uploader(
            "📤 Upload PDF Files", 
            type=['pdf'], 
            accept_multiple_files=True,
            key=f"pdf_upload_{subject}"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in [pdf['filename'] for pdf in subject_data['pdfs']]:
                    file_path = data_manager.save_pdf_file(
                        st.session_state.username, 
                        subject, 
                        uploaded_file.name, 
                        uploaded_file.read()
                    )
                    new_pdf = {
                        'filename': uploaded_file.name,
                        'path': file_path,
                        'progress': 0,
                        'current_page': 1,
                        'total_pages': 0,
                        'added_at': datetime.datetime.now().isoformat()
                    }
                    subject_data['pdfs'].append(new_pdf)
                    data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
                    st.success(f"PDF '{uploaded_file.name}' uploaded successfully!")
        
        # Display PDFs
        if subject_data['pdfs']:
            st.markdown(f"### 📄 Reading Section")
           
            for i, pdf in enumerate(subject_data['pdfs']):
                pdf_data , pdf_url = display_pdf_viewer(pdf['path'])
                
                toggle_key = f"show_pdf_{subject}_{i}"

                if toggle_key not in st.session_state:
                    st.session_state[toggle_key] = False
                                
                is_showing = st.session_state[toggle_key]
                button_text = f"❌ Hide {pdf['filename']}" if is_showing else f"📄 View {pdf['filename']}"                           
                

                with st.container():                    
                    col1, col2 , col3 , col4 = st.columns([0.6,0.1,0.2,0.1])                    
                    with col1:
                        # Toggle button
                        if st.button(button_text, key=f"pdf_toggle_{subject}_{i}",use_container_width=True):
                            st.session_state[toggle_key] = not st.session_state[toggle_key]
                            st.rerun()
                        # Add some spacing
                        if st.session_state[toggle_key]:                                            
                            components.html(f'''
                                <iframe src="{pdf_url}" width="100%" height="700px" type="application/pdf">
                                    <p>Your browser does not support PDFs. 
                                    <a href="{pdf_url}">Download the PDF</a>.</p>
                                </iframe>
                            ''', height=700)
                    with col2:
                         st.link_button("Open",url=pdf_url,use_container_width=True)                 
                                           
                    with col3:                        
                        st.download_button(                                
                            label="Download PDF",
                            data=pdf_data,
                            file_name=pdf['filename'],
                            key=f"download_pdf_{subject}_{i}",
                            mime="application/pdf",   
                            icon = ":material/download:" ,
                            use_container_width=True
                                                     
                        )
                    with col4:
                        if st.button("Delete", key=f"delete_pdf_{subject}_{i}",use_container_width=True):
                            del_pdf(subject,i,pdf,subject_data)

                           
        else:
            st.info("No PDF files uploaded yet. Upload your first PDF above!")
    
   
def render_analytics_dashboard():
    """Render comprehensive analytics dashboard"""
    st.header("📊 Study Analytics Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_subjects = len(st.session_state.user_data['subjects'])
    total_study_time = st.session_state.user_data['total_study_time']
    total_sessions = len(st.session_state.user_data['study_sessions'])
    
    total_videos = sum(len(subject['videos']) for subject in st.session_state.user_data['subjects'].values())
    total_playlists = sum(len(subject['playlists']) for subject in st.session_state.user_data['subjects'].values())
    total_pdfs = sum(len(subject['pdfs']) for subject in st.session_state.user_data['subjects'].values())
    
    with col1:
        st.metric("Total Subjects", total_subjects)
    with col2:
        st.metric("Study Time", format_time(int(total_study_time)))
    with col3:
        st.metric("Study Sessions", total_sessions)
    with col4:
        st.metric("Total Content", total_videos + total_playlists + total_pdfs)
    
    # print("user data",st.session_state.user_data)
    # Study time trends
    if st.session_state.user_data['study_sessions']:
    
        st.subheader("Study Time Trends")
        
        sessions_df = pd.DataFrame(st.session_state.user_data['study_sessions'])
        sessions_df['date'] = pd.to_datetime(sessions_df['date'])
        sessions_df['duration_minutes'] = sessions_df['duration'] / 60
        
        daily_study = sessions_df.groupby(sessions_df['date'].dt.date)['duration_minutes'].sum().reset_index()
        daily_study.columns = ['date', 'minutes']
        
        fig = px.line(
            daily_study,
            x='date',
            y='minutes',
            title='Daily Study Time (Minutes)',
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Weekly Study Summary")
        sessions_df['week'] = sessions_df['date'].dt.isocalendar().week
        weekly_study = sessions_df.groupby('week')['duration_minutes'].sum().reset_index()
        
        fig2 = px.bar(
            weekly_study,
            x='week',
            y='duration_minutes',
            title='Weekly Study Time (Minutes)'
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Subject-wise progress
    st.subheader("Subject-wise Progress")
    
    subject_stats = []
    for subject_name, subject_data in st.session_state.user_data['subjects'].items():
        total_content = len(subject_data['videos']) + len(subject_data['playlists']) + len(subject_data['pdfs'])
        completed_content = (
            sum(1 for v in subject_data['videos'] if v.get('progress', 0) == 100) +
            sum(1 for p in subject_data['playlists'] if p.get('progress', 0) == 100) +
            sum(1 for p in subject_data['pdfs'] if p.get('progress', 0) == 100)
        )
        
        progress = (completed_content / total_content * 100) if total_content > 0 else 0
        
        subject_stats.append({
            'Subject': subject_name,
            'Total Content': total_content,
            'Completed': completed_content,
            'Progress (%)': progress
        })
    
    if subject_stats:
        df = pd.DataFrame(subject_stats)
        
        fig3 = px.bar(
            df,
            x='Subject',
            y='Progress (%)',
            title='Subject Completion Progress',
            color='Progress (%)',
            color_continuous_scale='RdYlGn'
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)        
        st.subheader("Detailed Subject Statistics")
        st.dataframe(df, use_container_width=True)
    
    # Study habits analysis
    if st.session_state.user_data['study_sessions']:
        st.subheader("Study Habits Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            avg_duration = sessions_df['duration_minutes'].mean()
            st.metric("Average Session Duration", f"{avg_duration:.1f} minutes")
            
            day_productivity = sessions_df.groupby(sessions_df['date'].dt.day_name())['duration_minutes'].sum()
            most_productive_day = day_productivity.idxmax()
            st.metric("Most Productive Day", most_productive_day)
        
        with col2:
            current_week = datetime.datetime.now().isocalendar()[1]
            this_week_sessions = sessions_df[sessions_df['date'].dt.isocalendar().week == current_week]
            st.metric("This Week's Sessions", len(this_week_sessions))
            longest_session = sessions_df['duration_minutes'].max()
            st.metric("Longest Session", f"{longest_session:.1f} minutes")


def render_login_page():
    """Render login/register page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>📚 Welcome to Study Portal</h1>
        <p>Your comprehensive study companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.subheader("Login to Your Account")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_btn"):
                if username and password:
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        with tab2:
            st.subheader("Create New Account")
            new_username = st.text_input("Choose Username", key="register_username")
            new_password = st.text_input("Choose Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Register", key="register_btn"):
                if new_username and new_password and confirm_password:
                    if new_password == confirm_password:
                        if register_user(new_username, new_password):
                            st.success("Registration successful! You can now login.")
                        else:
                            st.error("Username already exists")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")


def main():
    """Main application function"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        render_login_page()
        return
    
    if 'user_data' not in st.session_state:
        st.session_state.user_data = data_manager.load_user_data(st.session_state.username)
    render_header()      
    render_sidebar()

    if st.session_state.get('show_analytics', False):
        render_analytics_dashboard()
        if st.button("🔙 Back to Subjects"):
            st.session_state.show_analytics = False
            st.rerun()
    else:
        render_subject_content()
        if st.button("📊 View Analytics Dashboard"):
            st.session_state.show_analytics = True
            st.rerun()
        
        

    
    if 'last_save' not in st.session_state:
        st.session_state.last_save = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_save > 60:  
        data_manager.save_user_data(st.session_state.username, st.session_state.user_data)
        st.session_state.last_save = current_time

if __name__ == "__main__":
    main()
