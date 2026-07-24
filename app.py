import streamlit as st
import os
import asyncio
import tempfile
import soundfile as sf
from gtts import gTTS
import edge_tts

# ==========================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN GLASSMORPHISM
# ==========================================
st.set_page_config(page_title="T2V - zZ", page_icon="🎙️", layout="centered")

def load_css():
    st.markdown("""
    <style>
    /* Hiệu ứng khung kính mờ (Glassmorphism) */
    .glass-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Làm mềm các ô nhập liệu */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }
    
    /* Nút bấm gradient hiện đại */
    .stButton > button {
        background: linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #121212 !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 201, 255, 0.4) !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 201, 255, 0.6) !important;
    }

    /* =========================================
       BỘ LỆNH ẨN GIAO DIỆN MẶC ĐỊNH CỦA STREAMLIT
       ========================================= */
    #MainMenu {visibility: hidden;} /* Ẩn menu 3 chấm góc phải */
    footer {visibility: hidden;}    /* Ẩn dòng chữ Built with Streamlit */
    header {visibility: hidden;}    /* Ẩn toàn bộ thanh header trên cùng */
    .stDeployButton {display:none;} /* Ẩn nút Deploy (nếu có) */
    </style>
    """, unsafe_allow_html=True)

load_css()

# ==========================================
# 2. XỬ LÝ LÕI AI (Tích hợp Cache)
# ==========================================
EDGE_VOICES = {
    "Tiếng Việt - HoaiMy (nữ)": "vi-VN-HoaiMyNeural",
    "Tiếng Việt - NamMinh (nam)": "vi-VN-NamMinhNeural",
    "English (US) - Jenny (nữ)": "en-US-JennyNeural",
    "English (US) - Guy (nam)": "en-US-GuyNeural",
    "English (UK) - Sonia (nữ)": "en-GB-SoniaNeural",
    "日本語 - Nanami (nữ)": "ja-JP-NanamiNeural",
    "中文 - Xiaoxiao (nữ)": "zh-CN-XiaoxiaoNeural"
}

# st.cache_resource giúp server chỉ tải model VieNeu đúng 1 lần
@st.cache_resource
def load_vieneu():
    try:
        from vieneu import Vieneu
        model = Vieneu()
        voices = model.list_preset_voices()
        return model, {v[0]: v[1] for v in voices}
    except Exception:
        return None, {}

v_tts, vieneu_map = load_vieneu()

def adjust_wav_speed(path, percent):
    if percent == 0: return
    try:
        data, sr = sf.read(path)
        factor = 1 + (percent / 100.0)
        new_sr = max(8000, int(sr * factor))
        sf.write(path, data, new_sr)
    except Exception:
        pass

async def gen_edge(text, voice_id, speed):
    rate_str = f"{'+' if speed >= 0 else ''}{speed}%"
    out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    comm = edge_tts.Communicate(text, voice_id, rate=rate_str)
    await comm.save(out)
    return out

# ==========================================
# 3. BỐ CỤC UI
# ==========================================
st.markdown('<div class="glass-container">', unsafe_allow_html=True)

st.title("🎙️ T2V - zZ")
st.markdown("*Ở đây có đọc chữ thành tiếng.*")

text_input = st.text_area("📝 Nội dung cần đọc", height=150, placeholder="Nhập văn bản vào đây...")
engine = st.radio("🗂️ Nguồn giọng đọc", ["Edge TTS", "VieNeu-TTS", "Google TTS"], horizontal=True)

# Tự động thay đổi menu cài đặt theo từng engine
if engine == "Edge TTS":
    col1, col2 = st.columns(2)
    with col1:
        edge_voice = st.selectbox("Giọng đọc", list(EDGE_VOICES.keys()))
    with col2:
        edge_speed = st.slider("Tốc độ đọc (%)", -50, 50, 0, step=5)
        
elif engine == "VieNeu-TTS":
    col1, col2 = st.columns(2)
    with col1:
        if v_tts:
            vieneu_voice = st.selectbox("Giọng đọc vùng miền", list(vieneu_map.keys()))
        else:
            st.error("Không tải được mô hình VieNeu trên server.")
            vieneu_voice = None
    with col2:
        vieneu_speed = st.slider("Tốc độ đọc (%)", -30, 30, 0, step=5)
        
else:
    gtts_slow = st.checkbox("🐢 Đọc tốc độ chậm", value=False)
    st.caption("Giọng chuẩn Google, dễ nghe nhưng không thể chọn vùng miền.")

# Nút Xử lý
if st.button("✨ TẠO GIỌNG ĐỌC", use_container_width=True):
    if not text_input.strip():
        st.warning("⚠️ Vui lòng nhập nội dung cần đọc!")
    elif len(text_input) > 5000:
        st.warning("⚠️ Văn bản quá dài (tối đa 5000 ký tự)!")
    else:
        with st.spinner("Hệ thống đang tổng hợp âm thanh, vui lòng chờ trong giây lát..."):
            try:
                audio_path = None
                if engine == "Edge TTS":
                    voice_id = EDGE_VOICES[edge_voice]
                    audio_path = asyncio.run(gen_edge(text_input, voice_id, edge_speed))
                    
                elif engine == "VieNeu-TTS":
                    if v_tts:
                        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
                        vid = vieneu_map.get(vieneu_voice)
                        audio = v_tts.infer(text_input, voice=vid) if vid else v_tts.infer(text_input)
                        v_tts.save(audio, audio_path)
                        adjust_wav_speed(audio_path, vieneu_speed)
                        
                else:
                    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                    tts = gTTS(text=text_input, lang="vi", slow=gtts_slow)
                    tts.save(audio_path)
                    
                if audio_path:
                    st.success("✅ Đã tạo giọng đọc thành công!")
                    st.audio(audio_path)
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
