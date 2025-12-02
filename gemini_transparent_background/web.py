import gradio as gr
import cv2
import numpy as np
import os
from .advanced import remove_background_advanced
from google import genai
from google.genai import types
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

def process_image(image, despill, feather, erode, dilate):
    if image is None:
        return None
    
    # Save temporary input file
    temp_input = "temp_input.png"
    temp_output = "temp_output.png"
    
    # Gradio passes image as numpy array (RGB)
    # OpenCV expects BGR
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(temp_input, image_bgr)
    
    try:
        # Always use Advanced mode
        remove_background_advanced(
            temp_input,
            temp_output,
            despill_strength=despill,
            feather_amount=int(feather),
            erode_iterations=int(erode),
            dilate_iterations=int(dilate)
        )
            
        # Read back the result
        # Gradio expects RGB or RGBA
        result_bgra = cv2.imread(temp_output, cv2.IMREAD_UNCHANGED)
        result_rgba = cv2.cvtColor(result_bgra, cv2.COLOR_BGRA2RGBA)
        
        return result_rgba
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        # Cleanup
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)

def generate_and_process(prompt, despill, feather, erode, dilate):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise gr.Error("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Append green background instruction
        full_prompt = f"{prompt}, isolated on a solid bright green background (#00FF00). No green on the subject."
        
        # Gemini models use generate_content for image generation
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=full_prompt,
        )
        
        # Handle response
        if response.text:
            print(f"Generated text instead of image: {response.text}")
            raise gr.Error(f"Generated text instead of image: {response.text}")
            
        image_data = None
        
        # Try to find image in parts
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    break
        
        if image_data:
            # Convert to numpy array for processing
            image_pil = Image.open(io.BytesIO(image_data))
            image_np = np.array(image_pil)
            
            # Process the image
            processed_image = process_image(image_np, despill, feather, erode, dilate)
            
            return image_np, processed_image
        else:
            print("No image generated in response")
            raise gr.Error("No image generated in response")

    except Exception as e:
        print(f"Generation Error: {e}")
        raise gr.Error(f"Generation Error: {e}")

def process_green_bg_conversion(image, prompt, despill, feather, erode, dilate):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise gr.Error("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
    
    if image is None:
        return None, None

    try:
        client = genai.Client(api_key=api_key)
        
        # Prepare prompt for background replacement
        full_prompt = f"{prompt}. Change the background to a solid bright green (#00FF00). Keep the subject exactly as is. High quality, photorealistic."
        
        # Convert numpy image to PIL for API
        image_pil = Image.fromarray(image)
        
        # Gemini models use generate_content for image editing/generation
        # We pass the image as input along with the prompt
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents=[full_prompt, image_pil],
        )
        
        # Handle response
        if response.text:
            print(f"Generated text instead of image: {response.text}")
            raise gr.Error(f"Generated text instead of image: {response.text}")
            
        image_data = None
        
        # Try to find image in parts
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    break
        
        if image_data:
            # Convert to numpy array for processing
            generated_pil = Image.open(io.BytesIO(image_data))
            generated_np = np.array(generated_pil)
            
            # Process the image (remove green background)
            processed_image = process_image(generated_np, despill, feather, erode, dilate)
            
            return generated_np, processed_image
        else:
            print("No image generated in response")
            raise gr.Error("No image generated in response")

    except Exception as e:
        print(f"Conversion Error: {e}")
        raise gr.Error(f"Conversion Error: {e}")

with gr.Blocks(title="Gemini Transparent Background") as demo:
    gr.Markdown("# Gemini Transparent Background (背景透過ツール)")
    gr.Markdown("Gemini Nano Banana Proなどで生成されたグリーンバック画像をアップロードして、背景を透過します。")
    
    with gr.Tabs():
        with gr.TabItem("画像をアップロード"):
            with gr.Row():
                with gr.Column():
                    input_image = gr.Image(label="入力画像 (Input)", type="numpy")
                    
                    with gr.Accordion("詳細設定", open=True):
                        gr.Markdown("### パラメータ調整")
                        despill = gr.Slider(minimum=0.0, maximum=1.0, value=0.7, label="緑被り除去 (Despill Strength)", info="被写体の縁に残る緑色の反射を除去する強さです。")
                        feather = gr.Slider(minimum=0, maximum=20, step=1, value=5, label="エッジぼかし (Feather Amount)", info="境界線を滑らかにする範囲です。")
                        erode = gr.Slider(minimum=0, maximum=5, step=1, value=0, label="収縮 (Erode Iterations)", info="マスク領域を少し小さくします。")
                        dilate = gr.Slider(minimum=0, maximum=5, step=1, value=1, label="膨張 (Dilate Iterations)", info="マスク領域を少し広げます。")
                    
                    submit_btn = gr.Button("背景を削除する", variant="primary")
                    
                with gr.Column():
                    output_image = gr.Image(label="出力画像 (Output)", type="numpy")
            
            submit_btn.click(
                fn=process_image,
                inputs=[input_image, despill, feather, erode, dilate],
                outputs=output_image
            )

        with gr.TabItem("Geminiで生成して透過"):
            gr.Markdown("### Gemini API (Nano Banana Pro) を使って画像を生成し、自動で背景を透過します")
            
            # Top Section: Controls
            with gr.Column():
                prompt_input = gr.Textbox(label="プロンプト (Prompt)", placeholder="例: A cute robot character, full body")
                
                with gr.Accordion("詳細設定", open=False):
                    despill_gen = gr.Slider(minimum=0.0, maximum=1.0, value=0.7, label="緑被り除去")
                    feather_gen = gr.Slider(minimum=0, maximum=20, step=1, value=5, label="エッジぼかし")
                    erode_gen = gr.Slider(minimum=0, maximum=5, step=1, value=0, label="収縮")
                    dilate_gen = gr.Slider(minimum=0, maximum=5, step=1, value=1, label="膨張")

                generate_btn = gr.Button("生成して透過する", variant="primary")
            
            # Bottom Section: Images (2 Columns)
            with gr.Row():
                with gr.Column():
                    gen_output_original = gr.Image(label="生成された画像 (Original)", type="numpy")
                with gr.Column():
                    gen_output_processed = gr.Image(label="透過後の画像 (Processed)", type="numpy")

            generate_btn.click(
                fn=generate_and_process,
                inputs=[prompt_input, despill_gen, feather_gen, erode_gen, dilate_gen],
                outputs=[gen_output_original, gen_output_processed]
            )

        with gr.TabItem("背景置換＆透過"):
            gr.Markdown("### 既存の画像の背景をGeminiで緑色にしてから、透過処理を行います")
            
            with gr.Column():
                input_image_rep = gr.Image(label="入力画像 (Input)", type="numpy")
                prompt_input_rep = gr.Textbox(label="プロンプト (Optional)", placeholder="例: Keep the cat, change background to green. (空欄でも可)", info="被写体を明示したい場合に記述してください。")
                
                with gr.Accordion("詳細設定", open=False):
                    despill_rep = gr.Slider(minimum=0.0, maximum=1.0, value=0.7, label="緑被り除去")
                    feather_rep = gr.Slider(minimum=0, maximum=20, step=1, value=5, label="エッジぼかし")
                    erode_rep = gr.Slider(minimum=0, maximum=5, step=1, value=0, label="収縮")
                    dilate_rep = gr.Slider(minimum=0, maximum=5, step=1, value=1, label="膨張")

                replace_btn = gr.Button("背景を緑にして透過する", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    rep_output_green = gr.Image(label="背景置換後 (Green BG)", type="numpy")
                with gr.Column():
                    rep_output_processed = gr.Image(label="透過後の画像 (Processed)", type="numpy")

            replace_btn.click(
                fn=process_green_bg_conversion,
                inputs=[input_image_rep, prompt_input_rep, despill_rep, feather_rep, erode_rep, dilate_rep],
                outputs=[rep_output_green, rep_output_processed]
            )

    gr.Markdown("""
    ### 使い方
    1. **画像をアップロード**: 手持ちのグリーンバック画像を処理します。
    2. **Geminiで生成して透過**: プロンプトを入力して画像を生成し、その場で背景透過します。
    3. **背景置換＆透過**: 手持ちの画像の背景をAIで緑色に変えてから、透過処理を行います。
       - 環境変数 `GEMINI_API_KEY` の設定が必要です。
    """)

if __name__ == "__main__":
    demo.launch()
