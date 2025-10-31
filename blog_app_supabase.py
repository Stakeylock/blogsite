import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="BlogSpace",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SUPABASE CONNECTION ====================

@st.cache_resource
def init_supabase_connection():
    """Initialize Supabase connection"""
    supabase_url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("Supabase credentials not found. Please add SUPABASE_URL and SUPABASE_KEY to .streamlit/secrets.toml or .env file")
        st.stop()
    
    return create_client(supabase_url, supabase_key)

supabase: Client = init_supabase_connection()

# ==================== DATABASE FUNCTIONS ====================

def hash_password(password):
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password, bio=""):
    """Create a new user"""
    try:
        hashed_pw = hash_password(password)
        response = supabase.table("users").insert({
            "username": username,
            "email": email,
            "password": hashed_pw,
            "bio": bio,
            "created_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        return False

def authenticate_user(username, password):
    """Authenticate a user and return their info"""
    try:
        hashed_pw = hash_password(password)
        response = supabase.table("users").select("id, username, email").eq("username", username).eq("password", hashed_pw).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        return None

def get_user_by_id(user_id):
    """Get user information by ID"""
    try:
        response = supabase.table("users").select("id, username, email, bio, created_at").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        return None

def update_user_profile(user_id, email, bio):
    """Update user profile information"""
    try:
        response = supabase.table("users").update({
            "email": email,
            "bio": bio
        }).eq("id", user_id).execute()
        return True
    except Exception as e:
        return False

def change_password(user_id, old_password, new_password):
    """Change user password"""
    try:
        user = get_user_by_id(user_id)
        old_hashed = hash_password(old_password)
        new_hashed = hash_password(new_password)
        
        # Verify old password
        response = supabase.table("users").select("password").eq("id", user_id).execute()
        if response.data and response.data[0]["password"] == old_hashed:
            supabase.table("users").update({"password": new_hashed}).eq("id", user_id).execute()
            return True
        return False
    except Exception as e:
        return False

def create_post(user_id, title, content, category):
    """Create a new blog post"""
    try:
        response = supabase.table("posts").insert({
            "user_id": user_id,
            "title": title,
            "content": content,
            "category": category,
            "views": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        return None

def get_all_posts():
    """Get all posts with author info"""
    try:
        response = supabase.table("posts").select("id, user_id, title, content, category, views, created_at, users(username)").order("created_at", ascending=False).execute()
        return response.data
    except Exception as e:
        return []

def get_post_by_id(post_id):
    """Get a specific post by ID"""
    try:
        response = supabase.table("posts").select("id, user_id, title, content, category, views, created_at, users(username)").eq("id", post_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        return None

def get_user_posts(user_id):
    """Get all posts by a specific user"""
    try:
        response = supabase.table("posts").select("id, title, content, category, views, created_at, users(username)").eq("user_id", user_id).order("created_at", ascending=False).execute()
        return response.data
    except Exception as e:
        return []

def update_post(post_id, title, content, category):
    """Update a blog post"""
    try:
        response = supabase.table("posts").update({
            "title": title,
            "content": content,
            "category": category,
            "updated_at": datetime.now().isoformat()
        }).eq("id", post_id).execute()
        return True
    except Exception as e:
        return False

def delete_post(post_id):
    """Delete a blog post and its comments"""
    try:
        # Delete comments first
        supabase.table("comments").delete().eq("post_id", post_id).execute()
        # Delete likes
        supabase.table("likes").delete().eq("post_id", post_id).execute()
        # Delete post
        supabase.table("posts").delete().eq("id", post_id).execute()
        return True
    except Exception as e:
        return False

def increment_view_count(post_id):
    """Increment view count for a post"""
    try:
        response = supabase.table("posts").select("views").eq("id", post_id).execute()
        if response.data:
            current_views = response.data[0]["views"]
            supabase.table("posts").update({"views": current_views + 1}).eq("id", post_id).execute()
    except:
        pass

def add_comment(post_id, user_id, content, parent_id=None):
    """Add a comment to a post"""
    try:
        response = supabase.table("comments").insert({
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "parent_id": parent_id,
            "created_at": datetime.now().isoformat()
        }).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        return None
    except Exception as e:
        return None

def get_comments(post_id):
    """Get all comments for a post"""
    try:
        response = supabase.table("comments").select("id, user_id, content, created_at, parent_id, users(username)").eq("post_id", post_id).order("created_at", ascending=True).execute()
        return response.data
    except Exception as e:
        return []

def add_like(post_id, user_id):
    """Add a like to a post"""
    try:
        response = supabase.table("likes").insert({
            "post_id": post_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        return False

def remove_like(post_id, user_id):
    """Remove a like from a post"""
    try:
        supabase.table("likes").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        return False

def get_like_count(post_id):
    """Get the number of likes for a post"""
    try:
        response = supabase.table("likes").select("id", count="exact").eq("post_id", post_id).execute()
        return response.count
    except:
        return 0

def check_user_liked(post_id, user_id):
    """Check if a user has liked a post"""
    try:
        response = supabase.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        return len(response.data) > 0
    except:
        return False

def get_comment_count(post_id):
    """Get the number of comments for a post"""
    try:
        response = supabase.table("comments").select("id", count="exact").eq("post_id", post_id).is_("parent_id", "null").execute()
        return response.count
    except:
        return 0

def get_total_users():
    """Get total number of users"""
    try:
        response = supabase.table("users").select("id", count="exact").execute()
        return response.count
    except:
        return 0

def get_total_posts():
    """Get total number of posts"""
    try:
        response = supabase.table("posts").select("id", count="exact").execute()
        return response.count
    except:
        return 0

def add_sample_data():
    """Add sample data to the database"""
    try:
        # Check if sample data already exists
        users_response = supabase.table("users").select("id").execute()
        if len(users_response.data) > 0:
            return
        
        # Add sample users
        users = [
            {"username": "john_doe", "email": "john@example.com", "password": hash_password("password123"), "bio": "Tech enthusiast and blogger", "created_at": datetime.now().isoformat()},
            {"username": "jane_smith", "email": "jane@example.com", "password": hash_password("password123"), "bio": "Travel writer and photographer", "created_at": datetime.now().isoformat()},
            {"username": "alex_coding", "email": "alex@example.com", "password": hash_password("password123"), "bio": "Software engineer and open source contributor", "created_at": datetime.now().isoformat()},
        ]
        
        supabase.table("users").insert(users).execute()
        
        # Get user IDs
        users_data = supabase.table("users").select("id").execute()
        user_ids = [u["id"] for u in users_data.data]
        
        # Add sample posts
        posts = [
            {"user_id": user_ids[0], "title": "Getting Started with Streamlit", "content": "Streamlit is an amazing framework for building data apps quickly. In this post, I'll explore the basics and best practices.", "category": "Technology", "views": 0, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"user_id": user_ids[1], "title": "Top 10 Travel Destinations in 2025", "content": "Planning your next adventure? Check out these incredible destinations that are perfect for 2025.", "category": "Travel", "views": 0, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"user_id": user_ids[0], "title": "Python Tips and Tricks", "content": "Discover some lesser-known Python features that can make your code more efficient and elegant.", "category": "Technology", "views": 0, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"user_id": user_ids[2], "title": "Open Source Contribution Guide", "content": "Contributing to open source projects can be intimidating at first. Here's a beginner-friendly guide to get started.", "category": "Technology", "views": 0, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"user_id": user_ids[1], "title": "The Ultimate Food Guide to Tokyo", "content": "Tokyo is a foodie's paradise. Let me take you through the best restaurants and street food spots I discovered.", "category": "Food", "views": 0, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
        ]
        
        supabase.table("posts").insert(posts).execute()
    except Exception as e:
        pass

# ==================== INITIALIZATION ====================

add_sample_data()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.page = 'home'
    st.session_state.selected_post_id = None
    st.session_state.search_query = ''
    st.session_state.selected_category = 'All'
    st.session_state.new_post_id = None

# ==================== STYLING ====================

st.markdown('''
<style>
    .post-card {
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        background-color: #f8f9fa;
        margin-bottom: 15px;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .post-card:hover {
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .category-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
    }
    .tech-badge { background-color: #e8f4f8; color: #0e6ba8; }
    .lifestyle-badge { background-color: #f4e8f8; color: #6a0572; }
    .travel-badge { background-color: #e8f8f0; color: #0b6623; }
    .food-badge { background-color: #f8f0e8; color: #8b4513; }
    .health-badge { background-color: #f0f8e8; color: #2f7c31; }
    .entertainment-badge { background-color: #f8e8f0; color: #9c1f5f; }
    .education-badge { background-color: #e8f0f8; color: #004e89; }
    .business-badge { background-color: #f8f4e8; color: #8b6f47; }
    .science-badge { background-color: #f0e8f8; color: #5a189a; }
    .other-badge { background-color: #e8e8e8; color: #333333; }
    .comment-item {
        padding: 15px;
        background-color: #f0f0f0;
        border-radius: 8px;
        margin-bottom: 10px;
        margin-left: 20px;
    }
    .reply-item {
        padding: 12px;
        background-color: #fafafa;
        border-radius: 6px;
        margin-bottom: 8px;
        margin-left: 40px;
        border-left: 3px solid #ddd;
    }
</style>
''', unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

def get_category_class(category):
    """Get CSS class for category badge"""
    mapping = {
        'Technology': 'tech-badge',
        'Lifestyle': 'lifestyle-badge',
        'Travel': 'travel-badge',
        'Food': 'food-badge',
        'Health': 'health-badge',
        'Entertainment': 'entertainment-badge',
        'Education': 'education-badge',
        'Business': 'business-badge',
        'Science': 'science-badge',
        'Other': 'other-badge'
    }
    return mapping.get(category, 'other-badge')

def format_date(date_str):
    """Format date string"""
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%b %d, %Y at %I:%M %p')
        return str(date_str)
    except:
        return date_str

def get_excerpt(content, length=150):
    """Get excerpt from content"""
    if len(content) > length:
        return content[:length] + '...'
    return content

def get_author_name(user_obj):
    """Extract author name from user object"""
    if isinstance(user_obj, dict) and 'username' in user_obj:
        return user_obj['username']
    return str(user_obj)

# ==================== SIDEBAR NAVIGATION ====================

st.sidebar.title("📝 BlogSpace")
st.sidebar.divider()

if st.session_state.logged_in:
    st.sidebar.success(f"👤 Welcome, {st.session_state.username}!")
    st.sidebar.divider()
    
    # Navigation menu
    st.sidebar.subheader("Navigation")
    col1, col2 = st.sidebar.columns(2)
    
    if col1.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'home'
        st.session_state.selected_post_id = None
        st.rerun()
    
    if col2.button("📚 Browse", use_container_width=True):
        st.session_state.page = 'browse'
        st.session_state.selected_post_id = None
        st.rerun()
    
    if col1.button("✍️ Create Post", use_container_width=True):
        st.session_state.page = 'create'
        st.rerun()
    
    if col2.button("📝 My Posts", use_container_width=True):
        st.session_state.page = 'my_posts'
        st.rerun()
    
    if col1.button("👤 Profile", use_container_width=True):
        st.session_state.page = 'profile'
        st.rerun()
    
    if col2.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.page = 'home'
        st.rerun()

else:
    if st.sidebar.button("🔐 Login / Signup", use_container_width=True):
        st.session_state.page = 'auth'
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📊 Stats")
col1, col2 = st.sidebar.columns(2)
col1.metric("Total Posts", get_total_posts())
col2.metric("Total Users", get_total_users())

# ==================== PAGES ====================

# HOME PAGE
def page_home():
    st.title("📝 BlogSpace")
    st.markdown("*A community platform for writers and readers*")
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search posts...", placeholder="Search by title or content")
    with col2:
        category = st.selectbox("Filter by category", 
                               ['All', 'Technology', 'Lifestyle', 'Travel', 'Food', 'Health', 
                                'Entertainment', 'Education', 'Business', 'Science', 'Other'],
                               label_visibility="collapsed")
    
    st.divider()
    
    posts = get_all_posts()
    
    if search:
        search_lower = search.lower()
        posts = [p for p in posts if search_lower in p['title'].lower() or search_lower in p['content'].lower()]
    
    if category != 'All':
        posts = [p for p in posts if p['category'] == category]
    
    if not posts:
        st.info("No posts found. Be the first to create one! ✍️")
    else:
        for post in posts[:10]:
            post_id = post['id']
            title = post['title']
            content = post['content']
            cat = post['category']
            views = post['views']
            created = post['created_at']
            author = get_author_name(post['users'])
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f'<div class="post-card">', unsafe_allow_html=True)
                
                if st.button(title, key=f"home_post_{post_id}", use_container_width=True):
                    st.session_state.selected_post_id = post_id
                    st.session_state.page = 'view_post'
                    st.rerun()
                
                st.markdown(f'<span class="category-badge {get_category_class(cat)}">{cat}</span>', 
                           unsafe_allow_html=True)
                st.caption(f"by **{author}** • {format_date(created)}")
                st.write(get_excerpt(content, 200))
                
                col_a, col_b, col_c = st.columns(3)
                col_a.caption(f"👁️ {views} views")
                col_b.caption(f"❤️ {get_like_count(post_id)} likes")
                col_c.caption(f"💬 {get_comment_count(post_id)} comments")
                
                st.markdown('</div>', unsafe_allow_html=True)

# BROWSE PAGE
def page_browse():
    st.title("📚 Browse All Posts")
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        category = st.selectbox("Category", 
                               ['All', 'Technology', 'Lifestyle', 'Travel', 'Food', 'Health', 
                                'Entertainment', 'Education', 'Business', 'Science', 'Other'])
    with col2:
        sort_by = st.selectbox("Sort by", 
                              ['Newest First', 'Oldest First', 'Most Viewed', 'Most Liked'])
    with col3:
        search = st.text_input("Search", placeholder="Search posts...")
    
    st.divider()
    
    posts = get_all_posts()
    
    if search:
        search_lower = search.lower()
        posts = [p for p in posts if search_lower in p['title'].lower() or search_lower in p['content'].lower()]
    
    if category != 'All':
        posts = [p for p in posts if p['category'] == category]
    
    # Sort
    if sort_by == 'Most Viewed':
        posts.sort(key=lambda x: x['views'], reverse=True)
    elif sort_by == 'Most Liked':
        posts.sort(key=lambda x: get_like_count(x['id']), reverse=True)
    elif sort_by == 'Oldest First':
        posts.reverse()
    
    if not posts:
        st.info("No posts found.")
    else:
        for post in posts:
            post_id = post['id']
            title = post['title']
            content = post['content']
            cat = post['category']
            views = post['views']
            created = post['created_at']
            author = get_author_name(post['users'])
            
            if st.button(title, key=f"browse_post_{post_id}"):
                st.session_state.selected_post_id = post_id
                st.session_state.page = 'view_post'
                st.rerun()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.caption(f"📝 {author}")
            col2.caption(f"🏷️ {cat}")
            col3.caption(f"👁️ {views}")
            col4.caption(f"❤️ {get_like_count(post_id)}")
            st.divider()

# CREATE POST PAGE
def page_create():
    st.title("✍️ Create New Post")
    st.divider()
    
    title = st.text_input("Post Title", placeholder="Enter your post title...", key="create_title")
    category = st.selectbox("Category", 
                           ['Technology', 'Lifestyle', 'Travel', 'Food', 'Health', 
                            'Entertainment', 'Education', 'Business', 'Science', 'Other'],
                           key="create_category")
    content = st.text_area("Content", placeholder="Write your story here...", height=300, key="create_content")
    
    if st.button("📤 Publish Post", use_container_width=True):
        if not title.strip():
            st.error("Please enter a title")
        elif not content.strip() or len(content) < 50:
            st.error("Content must be at least 50 characters")
        else:
            post_id = create_post(st.session_state.user_id, title, content, category)
            if post_id:
                st.session_state.new_post_id = post_id
                st.success("✅ Post published successfully!")
                st.balloons()
                
                col1, col2 = st.columns(2)
                if col1.button("View Your Post"):
                    st.session_state.selected_post_id = post_id
                    st.session_state.page = 'view_post'
                    st.rerun()
                if col2.button("Create Another"):
                    st.session_state.new_post_id = None
                    st.rerun()
            else:
                st.error("Error creating post")

# VIEW POST PAGE
def page_view_post():
    if not st.session_state.selected_post_id:
        st.warning("No post selected")
        return
    
    post = get_post_by_id(st.session_state.selected_post_id)
    if not post:
        st.error("Post not found")
        return
    
    post_id = post['id']
    user_id = post['user_id']
    title = post['title']
    content = post['content']
    category = post['category']
    views = post['views']
    created = post['created_at']
    author = get_author_name(post['users'])
    
    # Increment view count
    increment_view_count(post_id)
    
    if st.button("← Back to Posts"):
        st.session_state.selected_post_id = None
        st.session_state.page = 'home'
        st.rerun()
    
    st.title(title)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.caption(f"✍️ {author}")
    col2.caption(f"📅 {format_date(created)}")
    col3.caption(f"🏷️ {category}")
    col4.caption(f"👁️ {views + 1} views")
    
    st.markdown(f'<span class="category-badge {get_category_class(category)}">{category}</span>', 
               unsafe_allow_html=True)
    
    st.divider()
    st.write(content)
    st.divider()
    
    # Like section
    if st.session_state.logged_in:
        col1, col2, col3 = st.columns(3)
        liked = check_user_liked(post_id, st.session_state.user_id)
        like_count = get_like_count(post_id)
        
        if col1.button(f"{'❤️ Unlike' if liked else '🤍 Like'} ({like_count})", use_container_width=True):
            if liked:
                remove_like(post_id, st.session_state.user_id)
            else:
                add_like(post_id, st.session_state.user_id)
            st.rerun()
    
    # Comments section
    st.subheader(f"💬 Comments ({get_comment_count(post_id)})")
    st.divider()
    
    if st.session_state.logged_in:
        comment_text = st.text_area("Add your comment...", placeholder="Share your thoughts...", height=100, key=f"comment_{post_id}")
        if st.button("Post Comment", use_container_width=True):
            if comment_text.strip():
                add_comment(post_id, st.session_state.user_id, comment_text)
                st.success("Comment posted!")
                st.rerun()
    else:
        st.info("👤 Please log in to comment")
    
    # Display comments
    comments = get_comments(post_id)
    main_comments = [c for c in comments if c['parent_id'] is None]
    
    for comment in main_comments:
        comment_id = comment['id']
        user_id_c = comment['user_id']
        comment_text = comment['content']
        created_c = comment['created_at']
        parent_id = comment['parent_id']
        username_c = get_author_name(comment['users'])
        
        st.markdown(f'<div class="comment-item">', unsafe_allow_html=True)
        st.caption(f"**{username_c}** • {format_date(created_c)}")
        st.write(comment_text)
        
        # Show replies
        replies = [c for c in comments if c['parent_id'] == comment_id]
        if replies:
            for reply in replies:
                reply_id = reply['id']
                user_id_r = reply['user_id']
                reply_text = reply['content']
                created_r = reply['created_at']
                username_r = get_author_name(reply['users'])
                st.markdown(f'<div class="reply-item">', unsafe_allow_html=True)
                st.caption(f"**{username_r}** (reply) • {format_date(created_r)}")
                st.write(reply_text)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Reply button
        if st.session_state.logged_in:
            if st.button("Reply", key=f"reply_btn_{comment_id}"):
                reply_text = st.text_input("Your reply...", key=f"reply_input_{comment_id}")
                if reply_text.strip():
                    add_comment(post_id, st.session_state.user_id, reply_text, comment_id)
                    st.success("Reply posted!")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# MY POSTS PAGE
def page_my_posts():
    st.title("📝 My Posts")
    st.divider()
    
    posts = get_user_posts(st.session_state.user_id)
    
    if not posts:
        st.info("You haven't created any posts yet. Create one to get started! ✍️")
    else:
        st.metric("Total Posts", len(posts))
        st.divider()
        
        for post in posts:
            post_id = post['id']
            title = post['title']
            content = post['content']
            category = post['category']
            views = post['views']
            created = post['created_at']
            
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**{title}**")
            col2.caption(f"👁️ {views}")
            col3.caption(f"❤️ {get_like_count(post_id)}")
            col4.caption(f"💬 {get_comment_count(post_id)}")
            
            col1, col2, col3 = st.columns(3)
            
            if col1.button("View", key=f"view_{post_id}"):
                st.session_state.selected_post_id = post_id
                st.session_state.page = 'view_post'
                st.rerun()
            
            if col2.button("Edit", key=f"edit_btn_{post_id}"):
                st.session_state.edit_post_id = post_id
                st.session_state.page = 'edit_post'
                st.rerun()
            
            if col3.button("Delete", key=f"delete_btn_{post_id}"):
                delete_post(post_id)
                st.success("Post deleted")
                st.rerun()
            
            st.divider()

# EDIT POST PAGE
def page_edit_post():
    if not hasattr(st.session_state, 'edit_post_id'):
        st.warning("No post selected for editing")
        return
    
    post = get_post_by_id(st.session_state.edit_post_id)
    if not post:
        st.error("Post not found")
        return
    
    post_id = post['id']
    user_id = post['user_id']
    title = post['title']
    content = post['content']
    category = post['category']
    views = post['views']
    created = post['created_at']
    author = get_author_name(post['users'])
    
    st.title("✏️ Edit Post")
    st.divider()
    
    if st.button("← Back"):
        st.session_state.page = 'my_posts'
        st.rerun()
    
    new_title = st.text_input("Post Title", value=title, key="edit_title")
    new_category = st.selectbox("Category", 
                               ['Technology', 'Lifestyle', 'Travel', 'Food', 'Health', 
                                'Entertainment', 'Education', 'Business', 'Science', 'Other'],
                               index=['Technology', 'Lifestyle', 'Travel', 'Food', 'Health', 
                                     'Entertainment', 'Education', 'Business', 'Science', 'Other'].index(category),
                               key="edit_category")
    new_content = st.text_area("Content", value=content, height=300, key="edit_content")
    
    if st.button("Save Changes", use_container_width=True):
        if update_post(post_id, new_title, new_content, new_category):
            st.success("Post updated successfully!")
            st.session_state.page = 'my_posts'
            st.rerun()
        else:
            st.error("Error updating post")

# PROFILE PAGE
def page_profile():
    st.title("👤 My Profile")
    st.divider()
    
    user = get_user_by_id(st.session_state.user_id)
    if not user:
        st.error("User not found")
        return
    
    user_id = user['id']
    username = user['username']
    email = user['email']
    bio = user['bio']
    created_at = user['created_at']
    
    col1, col2 = st.columns(2)
    col1.metric("Username", username)
    col2.metric("Member Since", format_date(created_at))
    
    posts = get_user_posts(st.session_state.user_id)
    st.metric("Total Posts", len(posts))
    
    st.divider()
    st.subheader("Edit Profile")
    
    new_email = st.text_input("Email", value=email, key="profile_email")
    new_bio = st.text_area("Bio", value=bio, height=100, key="profile_bio")
    
    if st.button("Save Profile", use_container_width=True):
        if update_user_profile(st.session_state.user_id, new_email, new_bio):
            st.session_state.email = new_email
            st.success("Profile updated!")
            st.rerun()
    
    st.divider()
    st.subheader("Change Password")
    
    old_pw = st.text_input("Current Password", type="password", key="old_pw")
    new_pw = st.text_input("New Password", type="password", key="new_pw")
    confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_pw")
    
    if st.button("Change Password", use_container_width=True):
        if not old_pw or not new_pw or not confirm_pw:
            st.error("All fields required")
        elif new_pw != confirm_pw:
            st.error("Passwords don't match")
        elif len(new_pw) < 6:
            st.error("Password must be at least 6 characters")
        else:
            if change_password(st.session_state.user_id, old_pw, new_pw):
                st.success("Password changed successfully!")
            else:
                st.error("Current password is incorrect")

# LOGIN/SIGNUP PAGE
def page_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 BlogSpace")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login to your account")
            
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True):
                if not username or not password:
                    st.error("Please enter username and password")
                else:
                    result = authenticate_user(username, password)
                    if result:
                        st.session_state.logged_in = True
                        st.session_state.user_id = result['id']
                        st.session_state.username = result['username']
                        st.session_state.email = result['email']
                        st.session_state.page = 'home'
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            st.divider()
            st.info("Demo credentials:\nUsername: john_doe\nPassword: password123")
        
        with tab2:
            st.subheader("Create a new account")
            
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_bio = st.text_area("Bio (optional)", height=80, key="signup_bio")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            
            if st.button("Sign Up", use_container_width=True):
                if not new_username or not new_email or not new_password:
                    st.error("Please fill in all required fields")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                elif '@' not in new_email:
                    st.error("Please enter a valid email")
                else:
                    if create_user(new_username, new_email, new_password, new_bio):
                        st.success("Account created! Logging you in...")
                        # Auto-login
                        result = authenticate_user(new_username, new_password)
                        if result:
                            st.session_state.logged_in = True
                            st.session_state.user_id = result['id']
                            st.session_state.username = result['username']
                            st.session_state.email = result['email']
                            st.session_state.page = 'home'
                            st.rerun()
                    else:
                        st.error("Username or email already exists")

# ==================== MAIN APP ====================

def main():
    if not st.session_state.logged_in and st.session_state.page not in ['home', 'browse', 'auth']:
        st.session_state.page = 'home'
    
    if st.session_state.page == 'home':
        page_home()
    elif st.session_state.page == 'browse':
        page_browse()
    elif st.session_state.page == 'create':
        if st.session_state.logged_in:
            page_create()
        else:
            st.warning("Please log in to create a post")
            if st.button("Go to Login"):
                st.session_state.page = 'auth'
                st.rerun()
    elif st.session_state.page == 'view_post':
        page_view_post()
    elif st.session_state.page == 'my_posts':
        if st.session_state.logged_in:
            page_my_posts()
        else:
            st.warning("Please log in to view your posts")
    elif st.session_state.page == 'edit_post':
        if st.session_state.logged_in:
            page_edit_post()
        else:
            st.warning("Please log in to edit posts")
    elif st.session_state.page == 'profile':
        if st.session_state.logged_in:
            page_profile()
        else:
            st.warning("Please log in to view your profile")
    elif st.session_state.page == 'auth':
        page_auth()

if __name__ == '__main__':
    main()
