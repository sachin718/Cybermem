import streamlit as st
from PIL import Image
import os
import json
import re
import hashlib

# Optional import for speech recognition
try:
    import speech_recognition as sr
    SPEECH_ENABLED = True
except ImportError:
    SPEECH_ENABLED = False

DATA_FILE = "cybermem.json"
USER_FILE = "users.json"
IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Load saved topics
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# Save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load users
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# Save users
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Voice to text function
def record_voice():
    if not SPEECH_ENABLED:
        st.error("Speech recognition not supported in this environment.")
        return ""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak now")
        try:
            audio = recognizer.listen(source, timeout=5)
            st.success("Audio recorded, processing...")
            return recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            st.error("Listening timed out")
        except sr.UnknownValueError:
            st.error("Could not understand audio")
        except sr.RequestError as e:
            st.error(f"Speech recognition error: {e}")
    return ""

# Streamlit GUI
st.set_page_config(page_title="CyberMem - Hacking Notes", layout="centered")

# Dark theme styling only
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0e1117;
            color: #c9d1d9;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #00ffae;
        }
        .stButton>button {
            background-color: #161b22;
            color: #00ffae;
            border: 1px solid #00ffae;
        }
        .stTextInput>div>div>input {
            background-color: #161b22;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Login system
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

users = load_users()

if not st.session_state.logged_in:
    st.title("🔐 CyberMem Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
      
        if username in users and users[username] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

    if st.checkbox("New user? Register here"):
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            if new_user in users:
                st.warning("Username already exists")
            else:
                users[new_user] = hash_password(new_pass)
                save_users(users)
                st.success("User registered! Please login now.")
    st.stop()

# Main app starts after login
st.title("🧠 CyberMem - Your Hacking Memory")

menu = st.sidebar.selectbox("Menu", ["Add Topic", "Recall Topic", "Edit Topic", "Delete Topic", "List Topics", "Search Steps"])
data = load_data()

if menu == "Add Topic":
    st.subheader("➕ Add New Topic")
    topic = st.text_input("Topic name")

    input_options = ["Text", "Image"]
    if SPEECH_ENABLED:
        input_options.append("Voice")
    input_type = st.radio("Input type", input_options)

    steps = []
    image_path = ""

    if input_type == "Text":
        steps = st.text_area("Enter steps (one per line)").split("\n")
    elif input_type == "Image":
        image_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if image_file is not None:
            img = Image.open(image_file)
            safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)
            if not safe_topic:
                safe_topic = "unnamed"
            image_path = os.path.join(IMAGE_FOLDER, f"{safe_topic}.png")
            img.save(image_path)
            st.image(img, caption="Saved Image")
    elif input_type == "Voice" and SPEECH_ENABLED:
        if st.button("🎤 Start Voice Recording"):
            voice_text = record_voice()
            st.session_state["voice_text"] = voice_text

        voice_result = st.session_state.get("voice_text", "")
        if voice_result:
            st.text_area("Recognized Text", voice_result, height=150)
            steps = voice_result.strip().split("\n")

    if st.button("Save Topic"):
        if topic.strip() == "":
            st.error("Topic name cannot be empty.")
        elif topic in data:
            st.warning(f"Topic '{topic}' already exists. Please use a different name or delete it first.")
        else:
            entry = steps if steps else []
            if image_path:
                entry = [f"[Image stored at {image_path}]"]
            data[topic] = entry
            save_data(data)
            st.success(f"Topic '{topic}' saved successfully.")

elif menu == "Recall Topic":
    st.subheader("📂 Recall Topic")
    if not data:
        st.info("No topics saved yet.")
    else:
        topic = st.selectbox("Select a topic", list(data.keys()))
        if topic:
            st.markdown("### 🔍 Steps:")
            for i, step in enumerate(data[topic], 1):
                if step.startswith("[Image stored at"):
                    path = step.split("[")[1].split("]")[0].replace("Image stored at ", "")
                    if os.path.exists(path):
                        st.image(path, caption=f"Image for: {topic}")
                    else:
                        st.error("Image file not found")
                else:
                    st.markdown(f"**{i}.** {step}")

elif menu == "Edit Topic":
    st.subheader("✏️ Edit Existing Topic")
    if not data:
        st.info("No topics to edit.")
    else:
        topic = st.selectbox("Select a topic to edit", list(data.keys()))
        if topic:
            steps = data[topic]
            if steps and steps[0].startswith("[Image stored at"):
                st.warning("This topic is image-based. Delete and re-upload if you want to change it.")
            else:
                current_text = "\n".join(steps)
                new_text = st.text_area("Edit steps", value=current_text, height=200)

                if st.button("Save Changes"):
                    updated_steps = [line.strip() for line in new_text.split("\n") if line.strip() != ""]
                    data[topic] = updated_steps
                    save_data(data)
                    st.success(f"Topic '{topic}' updated.")

elif menu == "Delete Topic":
    st.subheader("🗑️ Delete Topic")
    if not data:
        st.info("No topics to delete.")
    else:
        topic = st.selectbox("Select topic to delete", list(data.keys()))
        if st.button(f"Confirm Delete '{topic}'"):
            if data[topic] and data[topic][0].startswith("[Image stored at"):
                img_path = data[topic][0].split("[")[1].split("]")[0].replace("Image stored at ", "")
                if os.path.exists(img_path):
                    os.remove(img_path)
            del data[topic]
            save_data(data)
            st.success(f"Topic '{topic}' deleted.")

elif menu == "List Topics":
    st.subheader("📋 All Saved Topics")
    if not data:
        st.info("No topics found.")
    else:
        for topic in sorted(data.keys()):
            st.markdown(f"- {topic}")

elif menu == "Search Steps":
    st.subheader("🔍 Search in All Topics")
    query = st.text_input("Enter keyword to search")
    if query:
        results = {}
        for topic, steps in data.items():
            matches = [s for s in steps if query.lower() in s.lower() and not s.startswith("[Image stored at")]
            if matches:
                results[topic] = matches

        if results:
            for topic, steps in results.items():
                st.markdown(f"### 🔎 Topic: {topic}")
                for step in steps:
                    st.markdown(f"- {step}")
        else:
            st.warning("No matches found.")
