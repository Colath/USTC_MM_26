import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
import gradio as gr
import pywt

# ==========================================
# 任务 1: SVD 分解算法 (手写)
# ==========================================
def custom_svd(A):
    ATA = np.dot(A.T, A)
    eigenvalues, V = np.linalg.eigh(ATA)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    V = V[:, idx]
    singular_values = np.sqrt(np.maximum(eigenvalues, 0))
    valid_idx = singular_values > 1e-10
    singular_values = singular_values[valid_idx]
    V = V[:, valid_idx]
    U = np.dot(A, V) / singular_values
    return U, singular_values, V.T

def compress_channel_svd(channel, k):
    U, Sigma, VT = custom_svd(channel)
    k = int(min(k, len(Sigma)))
    U_k = U[:, :k]
    Sigma_k = np.diag(Sigma[:k])
    VT_k = VT[:k, :]
    return np.clip(np.dot(U_k, np.dot(Sigma_k, VT_k)), 0, 255)

# ==========================================
# 任务 3 (Optional): DWT 小波压缩算法
# ==========================================
def compress_channel_dwt(channel, threshold):
    coeffs = pywt.wavedec2(channel, 'haar', level=2)
    coeffs_thresholded = list(coeffs)
    for i in range(1, len(coeffs_thresholded)):
        coeffs_thresholded[i] = tuple(
            pywt.threshold(detail, value=threshold, mode='hard') 
            for detail in coeffs_thresholded[i]
        )
    reconstructed = pywt.waverec2(coeffs_thresholded, 'haar')
    return np.clip(reconstructed, 0, 255)

# ==========================================
# 核心处理逻辑与指标计算
# ==========================================
def process_image(image, param_value, algorithm):
    if image is None:
        return None, "请先上传图片"
    
    img_array = np.array(image).astype(float)
    R, G, B = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
    
    if algorithm == "SVD (奇异值分解)":
        k = max(1, int(param_value))
        R_comp = compress_channel_svd(R, k)
        G_comp = compress_channel_svd(G, k)
        B_comp = compress_channel_svd(B, k)
        param_text = f"**当前参数:** 保留奇异值数量 k = {k}"
    else:
        threshold = param_value
        R_comp = compress_channel_dwt(R, threshold)
        G_comp = compress_channel_dwt(G, threshold)
        B_comp = compress_channel_dwt(B, threshold)
        param_text = f"**当前参数:** 小波高频过滤阈值 = {threshold:.1f}"
    
    comp_array = np.stack((R_comp, G_comp, B_comp), axis=2)
    comp_image = Image.fromarray(comp_array.astype(np.uint8))
    
    psnr_val = psnr(img_array, comp_array, data_range=255)
    ssim_val = ssim(img_array, comp_array, data_range=255, channel_axis=-1)
    
    # 增加及格线与优秀线参考说明
    metrics_text = (
        f"### 算法: {algorithm}\n"
        f"{param_text}\n\n"
        f"**PSNR (峰值信噪比):** {psnr_val:.2f} dB\n"
        f"> 💡 *参考线：> 30 dB 视觉上基本无明显失真 (及格)；> 40 dB 极好，肉眼难辨差异。*\n\n"
        f"**SSIM (结构相似性):** {ssim_val:.4f}\n"
        f"> 💡 *参考线：> 0.90 结构保持较好 (及格)；越接近 1.0 越完美。*"
    )
    
    return comp_image, metrics_text

# ==========================================
# 构建 GUI
# ==========================================
def build_gui():
    # 定义主题，但不在这里传入 Blocks
    theme = gr.themes.Soft(primary_hue="indigo")
    
    # 移除 theme=theme，解决 Gradio 6.0 的警告
    with gr.Blocks(title="图像压缩算法对比") as demo:
        gr.Markdown("# 🎨 SVD 与 DWT 图像压缩算法对比")
        gr.Markdown("本项目不仅手动实现了 SVD 分解，还加入了 Optional 要求的离散小波变换 (DWT) 作为对比。")
        
        with gr.Row():
            with gr.Column():
                input_img = gr.Image(type="pil", label="上传原图")
                algo_radio = gr.Radio(
                    choices=["SVD (奇异值分解)", "DWT (离散小波变换)"], 
                    value="SVD (奇异值分解)", 
                    label="选择压缩算法"
                )
                # 最大值调整为 500
                param_slider = gr.Slider(minimum=1, maximum=1000, step=1, value=50, label="调整参数 (SVD的k值 或 DWT的阈值)")
                run_btn = gr.Button("开始压缩", variant="primary")
                
            with gr.Column():
                output_img = gr.Image(type="pil", label="压缩后图像", format="png")
                metrics_box = gr.Markdown("等待处理...")

        run_btn.click(
            fn=process_image,
            inputs=[input_img, param_slider, algo_radio],
            outputs=[output_img, metrics_box]
        )
        
    return demo, theme

if __name__ == "__main__":
    app, app_theme = build_gui()
    # 将 theme 放在 launch 中传入，规范且不报错
    app.launch(inbrowser=True, theme=app_theme)