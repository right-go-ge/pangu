import gradio as gr
import json
import os
import sys
import copy
import random
import requests
import time
import base64
import uuid
import websocket
import threading
import logging
import traceback
from io import BytesIO
from PIL import Image
import shutil
import datetime
import platform
import subprocess

# 配置日志记录
# 修复Windows控制台编码问题
if platform.system() == 'Windows':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

log_file = "ttoi_error.log"
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 只输出到控制台，不写入文件
    ]
)

# 捕获未处理的异常
def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))
    # 继续使用系统默认的异常处理
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

# 记录启动信息
logging.info("=" * 50)
logging.info("程序启动")
try:
    logging.info(f"工作目录: {os.getcwd()}")
    if getattr(sys, 'frozen', False):
        logging.info(f"EXE路径: {sys.executable}")
        logging.info(f"EXE目录: {os.path.dirname(sys.executable)}")
except Exception as e:
    logging.error(f"获取路径信息时出错: {e}")

# ComfyUI服务器地址
COMFYUI_SERVER = "127.0.0.1:8188"  # 可以根据实际情况修改

# WSL路径常量
WSL_COMFYUI_PATH = "\\\\wsl$\\ComfyUI-Ubuntu\\home\\ComfyUI"

# 读取workflows.json文件
def load_workflow():
    # 首先尝试当前目录的json文件夹
    try:
        with open("json/workflows.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "json", "workflows.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到workflows.json文件，已尝试路径: json/workflows.json 和 {workflow_path}")
            raise

# 读取图生图工作流文件
def load_img2img_workflow():
    # 首先尝试当前目录的workflows文件夹
    try:
        with open("workflows/img_to_img.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "img_to_img.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到img_to_img.json文件，已尝试路径: workflows/img_to_img.json 和 {workflow_path}")
            raise

# 读取三视图工作流文件
def load_random_three_views_workflow():
    # 首先尝试当前目录的workflows文件夹
    try:
        with open("workflows/Random_three_views.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Random_three_views.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到Random_three_views.json文件，已尝试路径: workflows/Random_three_views.json 和 {workflow_path}")
            raise

# 读取放大及面部修复工作流文件
def load_magnified_facial_restoration_workflow():
    # 首先尝试当前目录的workflows文件夹
    try:
        with open("workflows/Magnified_facial_restoration.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Magnified_facial_restoration.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到Magnified_facial_restoration.json文件，已尝试路径: workflows/Magnified_facial_restoration.json 和 {workflow_path}")
            raise

# 保存workflows.json文件
def save_workflow_json(workflow_data):
    # 首先尝试当前目录的json文件夹
    try:
        with open("json/workflows.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "json", "workflows.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 保存图生图工作流文件
def save_img2img_workflow_json(workflow_data):
    # 首先尝试当前目录的workflows文件夹
    try:
        os.makedirs("workflows", exist_ok=True)
        with open("workflows/img_to_img.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "img_to_img.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 保存三视图工作流文件
def save_random_three_views_workflow_json(workflow_data):
    # 首先尝试当前目录的workflows文件夹
    try:
        os.makedirs("workflows", exist_ok=True)
        with open("workflows/Random_three_views.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Random_three_views.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 保存放大及面部修复工作流文件
def save_magnified_facial_restoration_workflow_json(workflow_data):
    # 首先尝试当前目录的workflows文件夹
    try:
        os.makedirs("workflows", exist_ok=True)
        with open("workflows/Magnified_facial_restoration.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Magnified_facial_restoration.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 加载工作流
workflow = load_workflow()

# 加载图生图工作流
try:
    img2img_workflow = load_img2img_workflow()
except Exception as e:
    logging.error(f"加载图生图工作流失败: {e}")
    img2img_workflow = {}  # 使用空字典作为默认值

# 加载三视图工作流
try:
    random_three_views_workflow = load_random_three_views_workflow()
except Exception as e:
    logging.error(f"加载三视图工作流失败: {e}")
    random_three_views_workflow = {}  # 使用空字典作为默认值

# 加载放大及面部修复工作流
try:
    magnified_facial_restoration_workflow = load_magnified_facial_restoration_workflow()
except Exception as e:
    logging.error(f"加载放大及面部修复工作流失败: {e}")
    magnified_facial_restoration_workflow = {}  # 使用空字典作为默认值

# 读取面部修复工作流文件
def load_facial_restoration_workflow():
    # 首先尝试当前目录的workflows文件夹
    try:
        with open("workflows/Facial_restoration.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Facial_restoration.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到Facial_restoration.json文件，已尝试路径: workflows/Facial_restoration.json 和 {workflow_path}")
            raise

# 保存面部修复工作流文件
def save_facial_restoration_workflow_json(workflow_data):
    # 首先尝试当前目录的workflows文件夹
    try:
        os.makedirs("workflows", exist_ok=True)
        with open("workflows/Facial_restoration.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Facial_restoration.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 加载面部修复工作流
try:
    facial_restoration_workflow = load_facial_restoration_workflow()
except Exception as e:
    logging.error(f"加载面部修复工作流失败: {e}")
    facial_restoration_workflow = {}  # 使用空字典作为默认值

# 获取模型文件列表的通用函数
def get_models_from_folder(folder_path, extensions=None, normalize=True):
    if extensions is None:
        extensions = ['.safetensors', '.ckpt', '.pt', '.pth', '.bin']
    
    models = []
    
    try:
        if os.path.exists(folder_path):
            # 遍历所有子文件夹
            for root, dirs, files in os.walk(folder_path):
                for model_file in files:
                    if any(model_file.lower().endswith(ext) for ext in extensions):
                        # 计算相对路径，用于模型加载
                        rel_path = os.path.relpath(os.path.join(root, model_file), folder_path)
                        # 使用正斜杠版本，确保WSL兼容性
                        if normalize:
                            rel_path = rel_path.replace('\\', '/')
                        if rel_path not in models:
                            models.append(rel_path)
        
        # 对列表进行排序，方便查找
        models.sort()
    except Exception as e:
        print(f"读取模型文件夹时出错: {e}")
        logging.error(f"读取模型文件夹时出错: {e}")
    
    return models

# 获取超分辨率检测模型列表
def get_ultralytics_models():
    ultralytics_path = os.path.join(WSL_COMFYUI_PATH, "models", "ultralytics")
    return get_models_from_folder(ultralytics_path, extensions=['.pt'])

# 获取模型列表
def get_models_list():
    models = {
        "unet": [],
        "clip": [],
        "vae": [],
        "lora": [],
        "controlnet": [],  # 添加ControlNet模型列表
        "ultralytics": []  # 添加ultralytics模型列表
    }
    
    # 尝试读取WSL路径下的模型
    try:
        # UNET模型路径
        unet_path = os.path.join(WSL_COMFYUI_PATH, "models", "unet")
        models["unet"] = get_models_from_folder(unet_path)
        
        # CLIP模型路径
        clip_path = os.path.join(WSL_COMFYUI_PATH, "models", "clip")
        models["clip"] = get_models_from_folder(clip_path)
        
        # VAE模型路径
        vae_path = os.path.join(WSL_COMFYUI_PATH, "models", "vae")
        models["vae"] = get_models_from_folder(vae_path)
        
        # LoRA模型路径
        lora_path = os.path.join(WSL_COMFYUI_PATH, "models", "loras")
        if os.path.exists(lora_path):
            # 首先添加"None"选项
            if "None" not in models["lora"]:
                models["lora"].append("None")
            for model_file in os.listdir(lora_path):
                if os.path.isfile(os.path.join(lora_path, model_file)) and model_file.endswith(('.safetensors', '.ckpt', '.pt', '.pth', '.bin')):
                    if model_file not in models["lora"]:
                        models["lora"].append(model_file)
        
        # ControlNet模型路径
        controlnet_path = os.path.join(WSL_COMFYUI_PATH, "models", "controlnet")
        models["controlnet"] = get_models_from_folder(controlnet_path)
        
        # Ultralytics模型路径
        ultralytics_path = os.path.join(WSL_COMFYUI_PATH, "models", "ultralytics")
        models["ultralytics"] = get_models_from_folder(ultralytics_path, extensions=['.pt'])
    
    except Exception as e:
        print(f"读取模型时出错: {e}")
        logging.error(f"读取模型时出错: {e}")
    
    # 确保每个类别至少有一个默认选项
    if not models["unet"]:
        models["unet"].append("FLUX/flux-dev.safetensors")
    
    if not models["clip"]:
        models["clip"].append("flux/t5xxl_fp16.safetensors")
        models["clip"].append("flux/clip_l.safetensors")
    
    if not models["vae"]:
        models["vae"].append("flux/ae.safetensors")
    
    if not models["controlnet"] and len(models["controlnet"]) == 0:
        models["controlnet"].append("flux/Shakker-Labs/diffusion_pytorch_model.safetensors")
    
    if not models["ultralytics"]:
        models["ultralytics"].append("bbox/face_yolov8m.pt")
    
    # 对每个列表进行排序，方便查找
    for key in models:
        models[key].sort()
    
    return models

# 提取可调节参数
def extract_adjustable_params():
    params = {}
    
    # 提取图像尺寸参数
    if "1" in workflow and "inputs" in workflow["1"]:
        params["width"] = workflow["1"]["inputs"].get("width", 512)
        params["height"] = workflow["1"]["inputs"].get("height", 512)
    
    # 提取采样器参数
    if "8" in workflow and "inputs" in workflow["8"]:
        params["sampler_name"] = workflow["8"]["inputs"].get("sampler_name", "euler")
    
    # 提取调度器参数
    if "9" in workflow and "inputs" in workflow["9"]:
        params["scheduler"] = workflow["9"]["inputs"].get("scheduler", "simple")
        params["steps"] = workflow["9"]["inputs"].get("steps", 20)
        params["denoise"] = workflow["9"]["inputs"].get("denoise", 1)
    
    # 提取随机噪声种子
    if "11" in workflow and "inputs" in workflow["11"]:
        params["noise_seed"] = workflow["11"]["inputs"].get("noise_seed", 0)
    
    # 提取引导参数
    if "14" in workflow and "inputs" in workflow["14"]:
        params["guidance"] = workflow["14"]["inputs"].get("guidance", 3.5)
    
    # 提取303节点参数（图片命名）
    if "303" in workflow and "inputs" in workflow["303"]:
        params["image_name"] = workflow["303"]["inputs"].get("text", "")
    else:
        params["image_name"] = ""
    
    # 提取模型参数 - 设置默认值为截图中的模型
    if "6" in workflow and "inputs" in workflow["6"]:
        params["unet_name"] = workflow["6"]["inputs"].get("unet_name", "FLUX/flux-dev.safetensors")
    else:
        params["unet_name"] = "FLUX/flux-dev.safetensors"
    
    if "5" in workflow and "inputs" in workflow["5"]:
        params["clip_name1"] = workflow["5"]["inputs"].get("clip_name1", "flux/t5xxl_fp16.safetensors")
        params["clip_name2"] = workflow["5"]["inputs"].get("clip_name2", "flux/clip_l.safetensors")
    else:
        params["clip_name1"] = "flux/t5xxl_fp16.safetensors"
        params["clip_name2"] = "flux/clip_l.safetensors"
    
    if "4" in workflow and "inputs" in workflow["4"]:
        params["vae_name"] = workflow["4"]["inputs"].get("vae_name", "flux/ae.safetensors")
    else:
        params["vae_name"] = "flux/ae.safetensors"
    
    # 提取LoRA参数
    if "12" in workflow and "inputs" in workflow["12"]:
        params["lora_01"] = workflow["12"]["inputs"].get("lora_01", "None")
        params["strength_01"] = workflow["12"]["inputs"].get("strength_01", 0.8)
        params["lora_02"] = workflow["12"]["inputs"].get("lora_02", "None")
        params["strength_02"] = workflow["12"]["inputs"].get("strength_02", 0.8)
        params["lora_03"] = workflow["12"]["inputs"].get("lora_03", "None")
        params["strength_03"] = workflow["12"]["inputs"].get("strength_03", 1)
        params["lora_04"] = workflow["12"]["inputs"].get("lora_04", "None")
        params["strength_04"] = workflow["12"]["inputs"].get("strength_04", 1)
    
    # 提取文本提示词
    if "33" in workflow and "inputs" in workflow["33"]:
        params["face_prompt"] = workflow["33"]["inputs"].get("text", "")
    
    if "36" in workflow and "inputs" in workflow["36"]:
        params["clothes_prompt"] = workflow["36"]["inputs"].get("text", "")
    
    if "37" in workflow and "inputs" in workflow["37"]:
        params["environment_prompt"] = workflow["37"]["inputs"].get("text", "")
    
    return params

# 获取ComfyUI的input文件夹中所有图片
def get_input_folder_images():
    comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
    os.makedirs(comfyui_input_path, exist_ok=True)
    
    image_files = []
    valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
    
    try:
        for file in os.listdir(comfyui_input_path):
            file_path = os.path.join(comfyui_input_path, file)
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in valid_extensions):
                # 只添加文件名，不添加完整路径
                image_files.append(file)
    except Exception as e:
        print(f"读取图片文件夹时出错: {e}")
    
    # 使用修改时间排序，最新的在前面
    image_files.sort(key=lambda x: os.path.getmtime(os.path.join(comfyui_input_path, x)), reverse=True)
    
    # 只返回文件名列表
    return image_files

# 当选择下拉菜单中的图片时调用
def select_existing_image(file_path):
    if not file_path or not os.path.exists(file_path):
        return None, "未选择图片", "图片尺寸: 未知"
    
    # 获取图片尺寸
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            dimension_text = f"图片尺寸: {width} x {height} 像素"
    except Exception as e:
        dimension_text = f"无法获取图片尺寸: {str(e)}"
    
    return file_path, f"已选择图片: {file_path}", dimension_text

# 提取图生图可调节参数
def extract_img2img_params():
    params = {}
    
    # 如果工作流为空，返回默认参数
    if not img2img_workflow:
        return {
            "width": 512,
            "height": 512,
            "sampler_name": "euler",
            "scheduler": "simple",
            "steps": 20,
            # 移除去噪强度参数，已由重绘幅度取代
            "guidance": 3.5,
            "noise_seed": 0,
            "lora_01": "None",
            "strength_01": 0.8,
            "lora_02": "None",
            "strength_02": 0.8,
            "lora_03": "None",
            "strength_03": 1,
            "lora_04": "None",
            "strength_04": 1,
            "face_prompt": "",
            "clothes_prompt": "",
            "environment_prompt": "",
            "unet_name": "FLUX/flux-dev.safetensors",
            "clip_name1": "flux/t5xxl_fp16.safetensors",
            "clip_name2": "flux/clip_l.safetensors",
            "vae_name": "flux/ae.safetensors",
            "redraw_strength": 0.75,  # 图生图重绘幅度参数，代替去噪强度
            "image_name": ""  # 添加图片命名参数
        }
    
    # 提取303节点参数（图片命名）
    if "303" in img2img_workflow and "inputs" in img2img_workflow["303"]:
        params["image_name"] = img2img_workflow["303"]["inputs"].get("text", "")
    else:
        params["image_name"] = ""
    
    # 提取图像尺寸参数
    if "1" in img2img_workflow and "inputs" in img2img_workflow["1"]:
        params["width"] = img2img_workflow["1"]["inputs"].get("width", 512)
        params["height"] = img2img_workflow["1"]["inputs"].get("height", 512)
    
    # 提取采样器参数 - 修改为节点77
    if "77" in img2img_workflow and "inputs" in img2img_workflow["77"]:
        params["sampler_name"] = img2img_workflow["77"]["inputs"].get("sampler_name", "euler")
    else:
        params["sampler_name"] = "euler"  # 设置默认值
    
    # 提取调度器参数 - 修改为节点78，移除去噪强度
    if "78" in img2img_workflow and "inputs" in img2img_workflow["78"]:
        params["scheduler"] = img2img_workflow["78"]["inputs"].get("scheduler", "simple")
        params["steps"] = img2img_workflow["78"]["inputs"].get("steps", 20)
        # 移除去噪强度提取
    else:
        params["scheduler"] = "simple"  # 设置默认值
        params["steps"] = 20  # 设置默认值
    
    # 提取图生图重绘幅度参数
    if "94" in img2img_workflow and "inputs" in img2img_workflow["94"]:
        # 从string字段提取数值
        redraw_strength_str = img2img_workflow["94"]["inputs"].get("string", "0.75")
        try:
            params["redraw_strength"] = float(redraw_strength_str)
        except ValueError:
            params["redraw_strength"] = 0.75  # 如果无法解析，使用默认值
    else:
        params["redraw_strength"] = 0.75  # 默认值
    
    # 提取随机噪声种子 - 固定从节点79提取
    if "79" in img2img_workflow and "inputs" in img2img_workflow["79"]:
        params["noise_seed"] = img2img_workflow["79"]["inputs"].get("noise_seed", 0)
        print(f"从图生图工作流79号节点读取随机种子: {params['noise_seed']}")
    else:
        params["noise_seed"] = 0  # 设置默认值
    
    # 提取引导参数 - 修改为节点80
    if "80" in img2img_workflow and "inputs" in img2img_workflow["80"]:
        params["guidance"] = img2img_workflow["80"]["inputs"].get("guidance", 3.5)
    else:
        params["guidance"] = 3.5  # 设置默认值
    
    # 提取模型参数
    if "87" in img2img_workflow and "inputs" in img2img_workflow["87"]:  # 使用正确的节点ID
        params["unet_name"] = img2img_workflow["87"]["inputs"].get("unet_name", "FLUX/flux-dev.safetensors")
    else:
        params["unet_name"] = "FLUX/flux-dev.safetensors"  # 设置默认值
    
    if "75" in img2img_workflow and "inputs" in img2img_workflow["75"]:  # 使用正确的节点ID
        params["clip_name1"] = img2img_workflow["75"]["inputs"].get("clip_name1", "flux/t5xxl_fp16.safetensors")
        params["clip_name2"] = img2img_workflow["75"]["inputs"].get("clip_name2", "flux/clip_l.safetensors")
    else:
        params["clip_name1"] = "flux/t5xxl_fp16.safetensors"  # 设置默认值
        params["clip_name2"] = "flux/clip_l.safetensors"  # 设置默认值
    
    if "84" in img2img_workflow and "inputs" in img2img_workflow["84"]:  # 使用正确的节点ID
        params["vae_name"] = img2img_workflow["84"]["inputs"].get("vae_name", "flux/ae.safetensors")
    else:
        params["vae_name"] = "flux/ae.safetensors"  # 设置默认值
    
    # 提取LoRA参数 - 固定从节点88提取
    if "88" in img2img_workflow and "inputs" in img2img_workflow["88"]:
        params["lora_01"] = img2img_workflow["88"]["inputs"].get("lora_01", "None")
        params["strength_01"] = img2img_workflow["88"]["inputs"].get("strength_01", 0.8)
        params["lora_02"] = img2img_workflow["88"]["inputs"].get("lora_02", "None")
        params["strength_02"] = img2img_workflow["88"]["inputs"].get("strength_02", 0.8)
        params["lora_03"] = img2img_workflow["88"]["inputs"].get("lora_03", "None")
        params["strength_03"] = img2img_workflow["88"]["inputs"].get("strength_03", 1)
        params["lora_04"] = img2img_workflow["88"]["inputs"].get("lora_04", "None")
        params["strength_04"] = img2img_workflow["88"]["inputs"].get("strength_04", 1)
        print(f"从图生图工作流88号节点读取LoRA参数")
    else:
        params["lora_01"] = "None"  # 设置默认值
        params["strength_01"] = 0.8
        params["lora_02"] = "None"
        params["strength_02"] = 0.8
        params["lora_03"] = "None"
        params["strength_03"] = 1
        params["lora_04"] = "None"
        params["strength_04"] = 1
    
    # 直接从图生图工作流中的特定节点提取提示词
    # 节点150：人物，景别，镜头，服饰
    if "150" in img2img_workflow and "inputs" in img2img_workflow["150"]:
        params["face_prompt"] = img2img_workflow["150"]["inputs"].get("text", "")
    else:
        params["face_prompt"] = ""
    
    # 节点151：场景
    if "151" in img2img_workflow and "inputs" in img2img_workflow["151"]:
        params["clothes_prompt"] = img2img_workflow["151"]["inputs"].get("text", "")
    else:
        params["clothes_prompt"] = ""
    
    # 节点152：动作
    if "152" in img2img_workflow and "inputs" in img2img_workflow["152"]:
        params["environment_prompt"] = img2img_workflow["152"]["inputs"].get("text", "")
    else:
        params["environment_prompt"] = ""
    
    return params

# 保存调整后的参数
def save_workflow(params):
    workflow_copy = copy.deepcopy(workflow)
    
    # 更新图像尺寸
    if "1" in workflow_copy:
        workflow_copy["1"]["inputs"]["width"] = params["width"]
        workflow_copy["1"]["inputs"]["height"] = params["height"]
    
    # 更新303节点参数（图片命名）
    if "303" in workflow_copy:
        if "inputs" not in workflow_copy["303"]:
            workflow_copy["303"]["inputs"] = {}
        workflow_copy["303"]["inputs"]["text"] = params["image_name"]
    
    # 更新采样器
    if "8" in workflow_copy:
        workflow_copy["8"]["inputs"]["sampler_name"] = params["sampler_name"]
    
    # 更新调度器
    if "9" in workflow_copy:
        workflow_copy["9"]["inputs"]["scheduler"] = params["scheduler"]
        workflow_copy["9"]["inputs"]["steps"] = params["steps"]
        workflow_copy["9"]["inputs"]["denoise"] = params["denoise"]
    
    # 更新随机噪声种子
    if "11" in workflow_copy:
        workflow_copy["11"]["inputs"]["noise_seed"] = params["noise_seed"]
    # 更新图生图工作流的79号节点随机种子
    if "79" in workflow_copy and "inputs" in workflow_copy["79"]:
        workflow_copy["79"]["inputs"]["noise_seed"] = params["noise_seed"]
        print(f"已将随机种子 {params['noise_seed']} 保存到图生图工作流79号节点")
    
    # 更新引导参数
    if "14" in workflow_copy:
        workflow_copy["14"]["inputs"]["guidance"] = params["guidance"]
    
    # 更新模型参数
    if "6" in workflow_copy and "unet_name" in params:
        workflow_copy["6"]["inputs"]["unet_name"] = params["unet_name"]
    
    if "5" in workflow_copy:
        if "clip_name1" in params:
            workflow_copy["5"]["inputs"]["clip_name1"] = params["clip_name1"]
        if "clip_name2" in params:
            workflow_copy["5"]["inputs"]["clip_name2"] = params["clip_name2"]
    
    if "4" in workflow_copy and "vae_name" in params:
        workflow_copy["4"]["inputs"]["vae_name"] = params["vae_name"]
    
    # 更新LoRA参数
    if "12" in workflow_copy:
        workflow_copy["12"]["inputs"]["lora_01"] = params["lora_01"]
        workflow_copy["12"]["inputs"]["strength_01"] = params["strength_01"]
        workflow_copy["12"]["inputs"]["lora_02"] = params["lora_02"]
        workflow_copy["12"]["inputs"]["strength_02"] = params["strength_02"]
        workflow_copy["12"]["inputs"]["lora_03"] = params["lora_03"]
        workflow_copy["12"]["inputs"]["strength_03"] = params["strength_03"]
        workflow_copy["12"]["inputs"]["lora_04"] = params["lora_04"]
        workflow_copy["12"]["inputs"]["strength_04"] = params["strength_04"]
    
    # 更新图生图工作流中的88号节点LoRA参数
    if "88" in workflow_copy and "inputs" in workflow_copy["88"]:
        workflow_copy["88"]["inputs"]["lora_01"] = params["lora_01"]
        workflow_copy["88"]["inputs"]["strength_01"] = params["strength_01"]
        workflow_copy["88"]["inputs"]["lora_02"] = params["lora_02"]
        workflow_copy["88"]["inputs"]["strength_02"] = params["strength_02"]
        workflow_copy["88"]["inputs"]["lora_03"] = params["lora_03"]
        workflow_copy["88"]["inputs"]["strength_03"] = params["strength_03"]
        workflow_copy["88"]["inputs"]["lora_04"] = params["lora_04"]
        workflow_copy["88"]["inputs"]["strength_04"] = params["strength_04"]
        print(f"已将LoRA参数保存到图生图工作流88号节点")
    
    # 更新文本提示词
    if "33" in workflow_copy:
        workflow_copy["33"]["inputs"]["text"] = params["face_prompt"]
    
    if "36" in workflow_copy:
        workflow_copy["36"]["inputs"]["text"] = params["clothes_prompt"]
    
    if "37" in workflow_copy:
        workflow_copy["37"]["inputs"]["text"] = params["environment_prompt"]
    
    # 保存工作流
    save_workflow_json(workflow_copy)
    return workflow_copy

# 保存图生图调整后的参数
def save_img2img_workflow(params):
    workflow_copy = copy.deepcopy(img2img_workflow)
    
    # 如果工作流为空，使用默认结构（需实际使用时根据img_to_img.json结构调整）
    if not workflow_copy:
        logging.warning("图生图工作流为空，无法保存参数")
        return workflow_copy
    
    # 更新303节点参数（图片命名）
    if "303" in workflow_copy:
        if "inputs" not in workflow_copy["303"]:
            workflow_copy["303"]["inputs"] = {}
        workflow_copy["303"]["inputs"]["text"] = params["image_name"]
    
    # 更新图像尺寸
    if "1" in workflow_copy:
        workflow_copy["1"]["inputs"]["width"] = params["width"]
        workflow_copy["1"]["inputs"]["height"] = params["height"]
    
    # 更新采样器 - 修改为节点77
    if "77" in workflow_copy:
        workflow_copy["77"]["inputs"]["sampler_name"] = params["sampler_name"]
    
    # 更新调度器 - 修改为节点78，移除去噪强度
    if "78" in workflow_copy:
        workflow_copy["78"]["inputs"]["scheduler"] = params["scheduler"]
        workflow_copy["78"]["inputs"]["steps"] = params["steps"]
        # 移除去噪强度设置
    
    # 更新图生图重绘幅度
    if "94" in workflow_copy:
        workflow_copy["94"]["inputs"]["string"] = str(params["redraw_strength"])
    
    # 更新随机噪声种子 - 固定使用节点79
    if "79" in workflow_copy:
        workflow_copy["79"]["inputs"]["noise_seed"] = params["noise_seed"]
        print(f"已将随机种子 {params['noise_seed']} 保存到图生图工作流79号节点")
    
    # 更新引导参数 - 修改为节点80
    if "80" in workflow_copy:
        workflow_copy["80"]["inputs"]["guidance"] = params["guidance"]
    
    # 更新模型参数
    if "87" in workflow_copy and "unet_name" in params:
        workflow_copy["87"]["inputs"]["unet_name"] = params["unet_name"]
    
    if "75" in workflow_copy:
        if "clip_name1" in params:
            workflow_copy["75"]["inputs"]["clip_name1"] = params["clip_name1"]
        if "clip_name2" in params:
            workflow_copy["75"]["inputs"]["clip_name2"] = params["clip_name2"]
    
    if "84" in workflow_copy and "vae_name" in params:
        workflow_copy["84"]["inputs"]["vae_name"] = params["vae_name"]
    
    # 更新LoRA参数 - 固定到节点88
    if "88" in workflow_copy:
        workflow_copy["88"]["inputs"]["lora_01"] = params["lora_01"]
        workflow_copy["88"]["inputs"]["strength_01"] = params["strength_01"]
        workflow_copy["88"]["inputs"]["lora_02"] = params["lora_02"]
        workflow_copy["88"]["inputs"]["strength_02"] = params["strength_02"]
        workflow_copy["88"]["inputs"]["lora_03"] = params["lora_03"]
        workflow_copy["88"]["inputs"]["strength_03"] = params["strength_03"]
        workflow_copy["88"]["inputs"]["lora_04"] = params["lora_04"]
        workflow_copy["88"]["inputs"]["strength_04"] = params["strength_04"]
        print(f"已将LoRA参数保存到图生图工作流88号节点")
    
    # 更新文本提示词到对应的节点
    # 节点150：人物，景别，镜头，服饰
    if "150" in workflow_copy and "inputs" in workflow_copy["150"]:
        workflow_copy["150"]["inputs"]["text"] = params["face_prompt"]
    
    # 节点151：场景
    if "151" in workflow_copy and "inputs" in workflow_copy["151"]:
        workflow_copy["151"]["inputs"]["text"] = params["clothes_prompt"]
    
    # 节点152：动作
    if "152" in workflow_copy and "inputs" in workflow_copy["152"]:
        workflow_copy["152"]["inputs"]["text"] = params["environment_prompt"]
    
    # 保存工作流
    save_img2img_workflow_json(workflow_copy)
    return workflow_copy

# 生成随机种子
def generate_random_seed():
    return random.randint(0, 1000000000000000)

# 使用WebSocket监听ComfyUI状态
class ComfyUIWebSocket:
    def __init__(self, client_id, prompt_id=None, on_image_generated=None, on_progress=None):
        self.client_id = client_id
        self.prompt_id = prompt_id
        self.ws = None
        self.on_image_generated = on_image_generated
        self.on_progress = on_progress  # 添加进度回调
        self.ws_url = f"ws://{COMFYUI_SERVER}/ws?clientId={client_id}"
        self.running = False
        self.generated_images = []
        self.execution_started = False
        self.execution_completed = False
        self.current_node = ""  # 当前执行节点
        self.connection_successful = False  # 添加连接状态标志
        self.last_progress_time = 0  # 添加最后一次进度更新时间
        self.max_retry_count = 3  # 添加最大重试次数
        self.retry_count = 0  # 当前重试次数
        
    def on_message(self, ws, message):
        try:
            print(f"收到WebSocket消息: {message[:100]}..." if len(message) > 100 else message)
            data = json.loads(message)
            
            # 记录最后一次收到消息的时间
            self.last_progress_time = time.time()
            self.connection_successful = True
            
            if data["type"] == "status":
                print(f"ComfyUI状态: {data.get('status', 'unknown')}")
                if self.on_progress and not self.execution_started:
                    self.on_progress(0.15, "已连接ComfyUI，等待工作流开始...")
                return
                
            # 只处理与当前prompt_id相关的消息
            if "data" in data and "prompt_id" in data["data"] and data["data"]["prompt_id"] != self.prompt_id:
                print(f"收到其他工作流的消息，已忽略. 当前: {self.prompt_id}, 收到: {data['data']['prompt_id']}")
                return
                
            # 对于没有data字段但有prompt_id字段的消息
            if "prompt_id" in data and data["prompt_id"] != self.prompt_id:
                print(f"收到其他工作流的消息，已忽略. 当前: {self.prompt_id}, 收到: {data['prompt_id']}")
                return
            
            if data["type"] == "execution_start":
                print(f"工作流开始执行: {self.prompt_id}")
                self.execution_started = True
                if self.on_progress:
                    self.on_progress(0.2, "工作流开始执行...")
                
            elif data["type"] == "executing":
                # 执行中，更新进度
                node_id = None
                # 检查是否有data字段包装
                if "data" in data and "node" in data["data"]:
                    node_id = data["data"].get("node", "unknown")
                elif "node" in data:
                    node_id = data.get("node", "unknown")
                
                if node_id:
                    self.current_node = node_id
                    print(f"正在执行节点: {node_id}")
                    # 更新UI进度
                    if self.on_progress:
                        # 根据节点ID判断执行阶段
                        progress_message = self._get_node_description(node_id)
                        self.on_progress(0.25, f"正在执行: {progress_message}")
                
            elif data["type"] == "progress":
                # 进度更新 - 处理不同格式的进度消息
                value = None
                max_value = None
                
                # 检查是否有data字段包装
                if "data" in data:
                    if "value" in data["data"] and "max" in data["data"]:
                        value = data["data"]["value"]
                        max_value = data["data"]["max"]
                else:
                    if "value" in data and "max" in data:
                        value = data["value"]
                        max_value = data["max"]
                
                if value is not None and max_value is not None:
                    progress_value = value / max_value
                    print(f"进度: {int(progress_value * 100)}% ({value}/{max_value})")
                    # 将实际进度传递给UI
                    if self.on_progress:
                        # 将进度映射到0.25-0.9区间
                        ui_progress = 0.25 + progress_value * 0.65
                        progress_message = self._get_node_description(self.current_node)
                        self.on_progress(ui_progress, f"进度: {int(progress_value * 100)}% - {progress_message}")
                    
            elif data["type"] == "executed":
                # 节点执行完毕 - 处理不同格式的消息
                node_id = None
                output = None
                
                # 检查是否有data字段包装
                if "data" in data:
                    if "node" in data["data"]:
                        node_id = data["data"]["node"]
                    if "output" in data["data"]:
                        output = data["data"]["output"]
                else:
                    if "node" in data:
                        node_id = data["node"]
                    if "output" in data:
                        output = data["output"]
                
                if node_id:
                    print(f"节点执行完毕: {node_id}")
                    
                if output and "images" in output:
                    for img_data in output["images"]:
                        if "filename" in img_data:
                            img_info = {
                                "filename": img_data["filename"],
                                "subfolder": img_data.get("subfolder", ""),
                                "type": img_data.get("type", "output")
                            }
                            self.generated_images.append(img_info)
                            print(f"检测到图像输出: {img_info['filename']}")
                            if self.on_progress:
                                self.on_progress(0.9, "图像生成完成，准备下载...")
                        
            elif data["type"] == "execution_cached" or data["type"] == "execution_complete":
                # 执行完成
                print(f"工作流执行完成: {self.prompt_id}")
                self.execution_completed = True
                if self.on_progress:
                    self.on_progress(0.95, "工作流执行完成，准备显示结果...")
        except Exception as e:
            print(f"处理WebSocket消息时出错: {e}")
            import traceback
            traceback.print_exc()
            
    def on_error(self, ws, error):
        print(f"WebSocket错误: {error}")
        # 记录错误时的时间，便于后续分析
        self.last_error_time = time.time()
        
    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket连接关闭: 代码={close_status_code}, 消息={close_msg}")
        self.running = False
        
        # 尝试重新连接（仅当还未达到最大重试次数且工作流未完成）
        if self.retry_count < self.max_retry_count and self.execution_started and not self.execution_completed:
            self.retry_count += 1
            print(f"尝试重新连接WebSocket (尝试 {self.retry_count}/{self.max_retry_count})")
            if self.on_progress:
                self.on_progress(0.85, f"WebSocket连接中断，正在尝试重新连接 ({self.retry_count}/{self.max_retry_count})...")
            self.start()
            return
        
        # 如果WebSocket关闭但我们有图像且执行已经开始，调用回调
        if self.execution_started and self.generated_images and self.on_image_generated:
            print("WebSocket关闭时有未处理的图像，现在处理它们")
            self.on_image_generated(self.generated_images)
        
    def on_open(self, ws):
        print(f"WebSocket连接已打开: {self.ws_url}")
        self.running = True
        self.connection_successful = True
        self.last_progress_time = time.time()
        
        if self.on_progress:
            self.on_progress(0.15, "WebSocket连接已建立，等待ComfyUI响应...")
        
        # 发送一个ping消息测试WebSocket是否正常工作
        try:
            ws.send(json.dumps({"type": "ping"}))
            print("已发送ping消息")
        except Exception as e:
            print(f"发送ping消息失败: {e}")
        
    def start(self):
        # 创建WebSocket连接
        websocket.enableTrace(True)  # 启用调试输出
        try:
            self.ws = websocket.WebSocketApp(self.ws_url,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close,
                                          on_open=self.on_open)
            
            # 启动WebSocket客户端线程
            self.thread = threading.Thread(target=self.ws.run_forever)
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            print(f"创建WebSocket连接失败: {e}")
            import traceback
            traceback.print_exc()
        
    def close(self):
        # 如果WebSocket还在运行且有图像，调用回调
        if self.running and self.generated_images and self.on_image_generated:
            print("关闭WebSocket前处理生成的图像")
            self.on_image_generated(self.generated_images)
            
        # 关闭WebSocket
        if self.ws:
            print("关闭WebSocket连接")
            self.ws.close()
        self.running = False
        
    # 根据节点ID返回更友好的描述
    def _get_node_description(self, node_id):
        node_descriptions = {
            "4": "加载VAE模型",
            "5": "加载CLIP模型",
            "6": "加载UNET模型",
            "12": "加载LoRA模型",
            "14": "处理文本提示词",
            "20": "处理文本",
            "7": "进行采样计算",
            "11": "生成随机噪声",
            "2": "VAE解码图像",
            "3": "保存图像"
        }
        return node_descriptions.get(node_id, f"处理节点 {node_id}")

# 发送工作流到ComfyUI并获取结果
def send_workflow_to_comfyui(workflow_data, progress=None, return_all_images=False, input_image_path=None):
    try:
        # 生成客户端ID
        client_id = str(uuid.uuid4())
        generated_images = []  # 存储所有生成的图像路径
        generation_event = threading.Event()
        
        # 记录当前进度的变量
        current_progress = {"value": 0.1, "message": "正在初始化..."}
        
        # 创建回调函数处理生成的图像
        def on_image_generated(images):
            if images:
                print(f"处理生成的图像: 发现 {len(images)} 张图片")
                
                # 存储所有图像
                all_saved_images = []
                
                for i, image_info in enumerate(images):
                    filename = image_info["filename"]
                    subfolder = image_info.get("subfolder", "")
                    img_type = image_info.get("type", "output")
                    
                    # 构建图像URL
                    image_url = f"http://{COMFYUI_SERVER}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                    print(f"生成的图像 {i+1} URL: {image_url}")
                    
                    try:
                        # 下载图像
                        print(f"开始下载图像 {i+1}: {image_url}")
                        response = requests.get(image_url)
                        if response.status_code == 200:
                            print(f"图像 {i+1} 下载成功，准备保存")
                            # 确保output文件夹存在
                            os.makedirs("output", exist_ok=True)
                            
                            # 使用时间戳创建文件名
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_filename = f"output/image_{timestamp}_{i+1}.png"
                            
                            # 保存图像
                            image = Image.open(BytesIO(response.content))
                            image.save(output_filename)
                            all_saved_images.append(image)
                            print(f"图像 {i+1} 已保存到: {output_filename}")
                        else:
                            print(f"图像 {i+1} 下载失败，状态码: {response.status_code}")
                            print(response.text[:200] if len(response.text) > 200 else response.text)
                    except Exception as e:
                        print(f"下载图像 {i+1} 失败: {e}")
                
                # 更新生成的图像列表
                generated_images.extend(all_saved_images)
                
                # 通知主线程图像已生成
                generation_event.set()
            else:
                print("没有找到生成的图像")
                generation_event.set()
        
        # 创建进度回调函数
        def on_progress_update(value, message):
            nonlocal current_progress
            current_progress["value"] = value
            current_progress["message"] = message
            
            print(f"WebSocket接收到进度更新: {value:.2f} - {message}")
            if progress is not None:
                try:
                    progress(value, message)
                    print(f"UI进度已更新: {value:.2f}")
                except Exception as e:
                    print(f"更新UI进度失败: {e}")
        
        # 更新进度 - 10%
        if progress is not None:
            progress(0.1, "正在连接ComfyUI...")
        
        # ComfyUI API地址
        api_url = f"http://{COMFYUI_SERVER}/api/prompt"
        
        # 使用深度复制避免修改原始数据
        workflow_copy = copy.deepcopy(workflow_data)
        
        # 处理输入图像路径，如果提供了
        if input_image_path and os.path.exists(input_image_path):
            print(f"处理工作流中的输入图像: {input_image_path}")
            # 获取文件名（不包含路径）
            filename = os.path.basename(input_image_path)
            
            # 检查所有可能包含图像路径的节点
            for node_id, node_data in workflow_copy.items():
                if "inputs" in node_data:
                    # LoadImage节点检查
                    if "image" in node_data["inputs"] and "class_type" in node_data and node_data["class_type"] == "LoadImage":
                        node_data["inputs"]["image"] = filename
                        print(f"已将图像文件名 {filename} 设置到节点 {node_id} 的image字段")
        
        # 准备API请求数据
        prompt_data = {
            "prompt": workflow_copy,
            "client_id": client_id
        }
        
        # 发送工作流并获取提示ID
        print(f"发送工作流到ComfyUI... ClientID: {client_id}")
        
        response = requests.post(api_url, json=prompt_data)
        
        if response.status_code != 200:
            print(f"提交工作流失败: {response.status_code}")
            print(response.text)
            if progress is not None:
                progress(1.0, "提交工作流失败，尝试查找最新图像...")
            return find_latest_image()
            
        prompt_id = response.json()["prompt_id"]
        print(f"成功提交工作流，Prompt ID: {prompt_id}")
        
        # 更新进度 - 15%
        if progress is not None:
            progress(0.15, "工作流已提交，正在建立WebSocket连接...")
        
        # 检查队列状态，确认工作流已入队
        queue_response = requests.get(f"http://{COMFYUI_SERVER}/api/queue")
        queue_data = queue_response.json()
        print(f"队列状态: {queue_data}")
        
        # 创建并启动WebSocket连接
        print(f"创建WebSocket连接，客户端ID: {client_id}")
        ws_client = ComfyUIWebSocket(client_id, prompt_id, on_image_generated, on_progress_update)
        ws_client.start()
        
        # 等待一会儿确保WebSocket连接建立
        print("等待WebSocket连接建立...")
        time.sleep(2)
        
        # 设置超时时间为10分钟，兼容低配置电脑
        timeout = 600  # 10分钟

        # 等待工作流执行完成
        start_time = time.time()
        websocket_check_time = time.time()
        progress_update_time = time.time()
        
        # 显示进度
        print(f"开始等待工作流执行，无超时限制")
        while not generation_event.is_set():
            current_time = time.time()
            
            # 每5秒检查一次WebSocket连接状态，如果WebSocket没有响应则使用HTTP API检查状态
            if current_time - websocket_check_time > 5:
                websocket_check_time = current_time
                
                # 如果WebSocket连接建立但超过15秒没有收到消息，使用HTTP API检查状态（从原来的10秒增加）
                if (not ws_client.connection_successful or 
                    (ws_client.last_progress_time > 0 and current_time - ws_client.last_progress_time > 15)):
                    print("WebSocket连接可能不活跃，使用HTTP API检查状态")
                    try:
                        # 检查队列状态
                        status_response = requests.get(f"http://{COMFYUI_SERVER}/api/queue")
                        queue_data = status_response.json()
                        is_executing = bool(queue_data.get("queue_running"))
                        print(f"HTTP API检查 - 队列状态: {'正在执行' if is_executing else '空队列'}")
                        
                        # 检查历史记录中是否有我们的工作流
                        history_response = requests.get(f"http://{COMFYUI_SERVER}/api/history")
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            if prompt_id in history_data:
                                print(f"在历史记录中找到工作流: {prompt_id}")
                                
                                # 检查是否已完成
                                prompt_info = history_data[prompt_id]
                                if "outputs" in prompt_info:
                                    outputs = prompt_info["outputs"]
                                    
                                    # 查找所有输出节点
                                    for node_id, node_output in outputs.items():
                                        if "images" in node_output:
                                            images = []
                                            for img_data in node_output["images"]:
                                                img_info = {
                                                    "filename": img_data["filename"],
                                                    "subfolder": img_data.get("subfolder", ""),
                                                    "type": "output"
                                                }
                                                images.append(img_info)
                                                
                                            if images:
                                                print(f"从历史记录中找到 {len(images)} 张图像")
                                                on_image_generated(images)
                                                break
                                
                                # 如果在历史记录中但没有输出，说明正在执行
                                elapsed = current_time - start_time
                                if not generation_event.is_set():
                                    # 使用经过的时间作为简单进度估计
                                    progress_percent = min(0.8, 0.25 + (elapsed / 300) * 0.55)  # 假设最长需要5分钟
                                    if progress is not None and not ws_client.execution_completed:
                                        progress(progress_percent, f"正在生成图像... (HTTP检查)")
                    except Exception as e:
                        print(f"HTTP API检查失败: {e}")
                        import traceback
                        traceback.print_exc()
            
            # 每0.5秒从当前进度变量更新一次UI，确保UI总能得到更新
            if current_time - progress_update_time > 0.5:
                progress_update_time = current_time
                if progress is not None and current_progress["value"] > 0.15:
                    try:
                        progress(current_progress["value"], current_progress["message"])
                        print(f"定期更新UI进度: {current_progress['value']:.2f} - {current_progress['message']}")
                    except Exception as e:
                        print(f"定期更新UI进度失败: {e}")
            
            time.sleep(0.1)
            
        # 如果已过超时时间但还未收到图像
        if not generation_event.is_set():
            print("等待超时，尝试最后一次获取图像")
            
            # 尝试通过HTTP API获取最新的历史记录
            try:
                print("尝试通过HTTP API查询历史记录获取图像")
                history_response = requests.get(f"http://{COMFYUI_SERVER}/api/history")
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    if prompt_id in history_data:
                        print(f"在历史记录中找到工作流: {prompt_id}")
                        
                        # 检查输出
                        prompt_info = history_data[prompt_id]
                        if "outputs" in prompt_info:
                            outputs = prompt_info["outputs"]
                            
                            # 查找所有输出节点
                            for node_id, node_output in outputs.items():
                                if "images" in node_output:
                                    images = []
                                    for img_data in node_output["images"]:
                                        img_info = {
                                            "filename": img_data["filename"],
                                            "subfolder": img_data.get("subfolder", ""),
                                            "type": "output"
                                        }
                                        images.append(img_info)
                                        
                                    if images:
                                        print(f"从历史记录中找到 {len(images)} 张图像")
                                        on_image_generated(images)
                                        generation_event.set()
                                        break
            except Exception as e:
                print(f"通过HTTP API查询历史记录失败: {e}")
            
            if not generation_event.is_set():
                if progress is not None:
                    progress(0.95, "等待超时，尝试查找最新保存的图像...")
                result = find_latest_image()
                if return_all_images and result:
                    generated_images.append(result)
                
        # 确保WebSocket已关闭
        print("关闭WebSocket连接")
        if ws_client.running:
            ws_client.close()
        
        # 返回结果图像
        if generated_images:
            if return_all_images:
                print(f"返回所有 {len(generated_images)} 张生成的图像")
                return generated_images
            else:
                print("返回第一张生成的图像")
                return generated_images[0]
        else:
            print("没有图像生成，返回None")
            return None
        
    except Exception as e:
        print(f"与ComfyUI接口通信错误: {str(e)}")
        import traceback
        traceback.print_exc()
        # 记录到日志文件
        logging.error(f"与ComfyUI接口通信错误: {str(e)}")
        logging.error(traceback.format_exc())
        # 更新进度 - 错误状态
        if progress is not None:
            progress(1.0, f"错误: {str(e)}")
        # 出错时尝试查找最近保存的图像
        latest_image = find_latest_image()
        if return_all_images and latest_image:
            return [latest_image]
        return latest_image

# 发送图生图工作流到ComfyUI并获取结果
def send_img2img_workflow_to_comfyui(workflow_data, input_image_path=None, progress=None):
    try:
        # 验证输入图像
        if not input_image_path or not os.path.exists(input_image_path):
            error_msg = f"输入图像无效或不存在: {input_image_path}"
            logging.error(error_msg)
            if progress:
                progress(1.0, error_msg)
            return None
        
        # 检查文件类型是否为图像
        valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
        file_ext = os.path.splitext(input_image_path)[1].lower()
        if file_ext not in valid_extensions:
            error_msg = f"不支持的图像文件类型: {file_ext}，支持的类型: {', '.join(valid_extensions)}"
            logging.error(error_msg)
            if progress:
                progress(1.0, error_msg)
            return None
        
        # 生成客户端ID
        client_id = str(uuid.uuid4())
        generated_image_path = [None]  # 使用列表存储图像路径，以便在回调中修改
        generation_event = threading.Event()
        
        # 记录当前进度的变量
        current_progress = {"value": 0.1, "message": "正在初始化..."}
        
        # 创建回调函数处理生成的图像
        def on_image_generated(images):
            if images:
                print(f"处理生成的图像: 发现 {len(images)} 张图片")
                image_info = images[0]  # 获取第一张图像的信息
                filename = image_info["filename"]
                subfolder = image_info.get("subfolder", "")
                img_type = image_info.get("type", "output")
                
                # 构建图像URL
                image_url = f"http://{COMFYUI_SERVER}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
                print(f"生成的图像URL: {image_url}")
                
                try:
                    # 下载图像
                    print(f"开始下载图像: {image_url}")
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        print("图像下载成功，准备保存")
                        # 确保output文件夹存在
                        os.makedirs("output", exist_ok=True)
                        
                        # 使用时间戳创建文件名
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_filename = f"output/img2img_{timestamp}.png"
                        
                        # 保存图像
                        image = Image.open(BytesIO(response.content))
                        image.save(output_filename)
                        generated_image_path[0] = output_filename
                        print(f"图像已保存到: {output_filename}")
                        
                        # 通知主线程图像已生成
                        generation_event.set()
                    else:
                        print(f"图像下载失败，状态码: {response.status_code}")
                        print(response.text[:200] if len(response.text) > 200 else response.text)
                except Exception as e:
                    print(f"下载图像失败: {e}")
                    generation_event.set()
            else:
                print("没有找到生成的图像")
                generation_event.set()
        
        # 创建进度回调函数
        def on_progress_update(value, message):
            nonlocal current_progress
            current_progress["value"] = value
            current_progress["message"] = message
            
            print(f"WebSocket接收到进度更新: {value:.2f} - {message}")
            if progress is not None:
                try:
                    progress(value, message)
                    print(f"UI进度已更新: {value:.2f}")
                except Exception as e:
                    print(f"更新UI进度失败: {e}")
        
        # 更新进度 - 10%
        if progress is not None:
            progress(0.1, "正在准备输入图像...")
        
        # 处理输入图像
        try:
            # 找到图生图工作流中的图像加载节点
            image_node_found = False
            
            # 可能的图像输入节点ID列表 - 根据实际工作流调整
            possible_image_node_ids = ["2", "3", "10", "82", "image_loader"]
            
            # 获取文件名（不包含路径）
            filename = os.path.basename(input_image_path)
            
            # 使用深度复制避免修改原始数据
            workflow_copy = copy.deepcopy(workflow_data)
            
            for node_id in possible_image_node_ids:
                if node_id in workflow_copy and "inputs" in workflow_copy[node_id]:
                    if "image" in workflow_copy[node_id]["inputs"]:
                        # 使用文件名而不是base64编码的图像数据
                        workflow_copy[node_id]["inputs"]["image"] = filename
                        print(f"已将输入图像文件名 {filename} 添加到工作流节点 {node_id}")
                        image_node_found = True
                        break
            
            if not image_node_found:
                # 搜索所有节点，查找包含image字段的节点
                for node_id, node_data in workflow_copy.items():
                    if "inputs" in node_data:
                        if "image" in node_data["inputs"]:
                            node_data["inputs"]["image"] = filename
                            print(f"通过搜索找到图像节点 {node_id}，已设置文件名 {filename}")
                            image_node_found = True
                            break
            
            if not image_node_found:
                error_msg = "错误：无法在工作流中找到图像输入节点"
                print(error_msg)
                if progress is not None:
                    progress(1.0, error_msg)
                return None
                
        except Exception as e:
            error_msg = f"处理输入图像时出错: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            if progress is not None:
                progress(1.0, error_msg)
            return None
        
        # 更新进度 - 15%
        if progress is not None:
            progress(0.15, "正在连接ComfyUI...")
        
        # ComfyUI API地址
        api_url = f"http://{COMFYUI_SERVER}/api/prompt"
        
        # 准备API请求数据
        prompt_data = {
            "prompt": workflow_copy,
            "client_id": client_id
        }
        
        # 发送工作流并获取提示ID
        print(f"发送图生图工作流到ComfyUI... ClientID: {client_id}")
        
        try:
            response = requests.post(api_url, json=prompt_data, timeout=10)  # 添加超时
            
            if response.status_code != 200:
                error_msg = f"提交图生图工作流失败: {response.status_code}"
                print(error_msg)
                print(response.text)
                if progress is not None:
                    progress(1.0, error_msg)
                return find_latest_image()
                
            prompt_id = response.json()["prompt_id"]
            print(f"成功提交图生图工作流，Prompt ID: {prompt_id}")
        except requests.exceptions.RequestException as e:
            error_msg = f"连接ComfyUI服务器失败: {e}"
            print(error_msg)
            if progress is not None:
                progress(1.0, error_msg)
            return find_latest_image()
        
        # 更新进度 - 15%
        if progress is not None:
            progress(0.15, "工作流已提交，正在建立WebSocket连接...")
        
        # 检查队列状态，确认工作流已入队
        queue_response = requests.get(f"http://{COMFYUI_SERVER}/api/queue")
        queue_data = queue_response.json()
        print(f"队列状态: {queue_data}")
        
        # 创建并启动WebSocket连接
        print(f"创建WebSocket连接，客户端ID: {client_id}")
        ws_client = ComfyUIWebSocket(client_id, prompt_id, on_image_generated, on_progress_update)
        ws_client.start()
        
        # 等待一会儿确保WebSocket连接建立
        print("等待WebSocket连接建立...")
        time.sleep(2)
        
        # 设置超时时间为10分钟，兼容低配置电脑
        timeout = 600  # 10分钟

        # 等待工作流执行完成
        start_time = time.time()
        websocket_check_time = time.time()
        progress_update_time = time.time()
        
        # 显示进度
        print(f"开始等待工作流执行，超时时间: {timeout}秒")
        while not generation_event.is_set() and time.time() - start_time < timeout:
            current_time = time.time()
            
            # 每5秒检查一次WebSocket连接状态，如果WebSocket没有响应则使用HTTP API检查状态
            if current_time - websocket_check_time > 5:
                websocket_check_time = current_time
                
                # 如果WebSocket连接建立但超过15秒没有收到消息，使用HTTP API检查状态（从原来的10秒增加）
                if (not ws_client.connection_successful or 
                    (ws_client.last_progress_time > 0 and current_time - ws_client.last_progress_time > 15)):
                    print("WebSocket连接可能不活跃，使用HTTP API检查状态")
                    try:
                        # 检查队列状态
                        status_response = requests.get(f"http://{COMFYUI_SERVER}/api/queue")
                        queue_data = status_response.json()
                        is_executing = bool(queue_data.get("queue_running"))
                        print(f"HTTP API检查 - 队列状态: {'正在执行' if is_executing else '空队列'}")
                        
                        # 检查历史记录中是否有我们的工作流
                        history_response = requests.get(f"http://{COMFYUI_SERVER}/api/history")
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            if prompt_id in history_data:
                                print(f"在历史记录中找到工作流: {prompt_id}")
                                
                                # 检查是否已完成
                                prompt_info = history_data[prompt_id]
                                if "outputs" in prompt_info:
                                    outputs = prompt_info["outputs"]
                                    
                                    # 查找所有输出节点
                                    for node_id, node_output in outputs.items():
                                        if "images" in node_output:
                                            images = []
                                            for img_data in node_output["images"]:
                                                img_info = {
                                                    "filename": img_data["filename"],
                                                    "subfolder": img_data.get("subfolder", ""),
                                                    "type": "output"
                                                }
                                                images.append(img_info)
                                                
                                            if images:
                                                print(f"从历史记录中找到 {len(images)} 张图像")
                                                on_image_generated(images)
                                                break
                                
                                # 如果在历史记录中但没有输出，说明正在执行
                                elapsed = current_time - start_time
                                if not generation_event.is_set():
                                    # 使用经过的时间作为简单进度估计
                                    progress_percent = min(0.8, 0.25 + (elapsed / 300) * 0.55)  # 假设最长需要5分钟
                                    if progress is not None and not ws_client.execution_completed:
                                        progress(progress_percent, f"正在生成图像... (HTTP检查)")
                    except Exception as e:
                        print(f"HTTP API检查失败: {e}")
                        import traceback
                        traceback.print_exc()
            
            # 每0.5秒从当前进度变量更新一次UI，确保UI总能得到更新
            if current_time - progress_update_time > 0.5:
                progress_update_time = current_time
                if progress is not None and current_progress["value"] > 0.15:
                    try:
                        progress(current_progress["value"], current_progress["message"])
                        print(f"定期更新UI进度: {current_progress['value']:.2f} - {current_progress['message']}")
                    except Exception as e:
                        print(f"定期更新UI进度失败: {e}")
            
            time.sleep(0.1)
            
        # 如果已过超时时间但还未收到图像
        if not generation_event.is_set():
            print("等待超时，尝试最后一次获取图像")
            
            # 尝试通过HTTP API获取最新的历史记录
            try:
                print("尝试通过HTTP API查询历史记录获取图像")
                history_response = requests.get(f"http://{COMFYUI_SERVER}/api/history")
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    if prompt_id in history_data:
                        print(f"在历史记录中找到工作流: {prompt_id}")
                        
                        # 检查输出
                        prompt_info = history_data[prompt_id]
                        if "outputs" in prompt_info:
                            outputs = prompt_info["outputs"]
                            
                            # 查找所有输出节点
                            for node_id, node_output in outputs.items():
                                if "images" in node_output:
                                    images = []
                                    for img_data in node_output["images"]:
                                        img_info = {
                                            "filename": img_data["filename"],
                                            "subfolder": img_data.get("subfolder", ""),
                                            "type": "output"
                                        }
                                        images.append(img_info)
                                        
                                    if images:
                                        print(f"从历史记录中找到 {len(images)} 张图像")
                                        on_image_generated(images)
                                        generation_event.set()
                                        break
            except Exception as e:
                print(f"通过HTTP API查询历史记录失败: {e}")
            
            if not generation_event.is_set():
                if progress is not None:
                    progress(0.95, "等待超时，尝试查找最新保存的图像...")
                result = find_latest_image()
                if result:
                    generated_image_path[0] = result
                
        # 确保WebSocket已关闭
        print("关闭WebSocket连接")
        if ws_client.running:
            ws_client.close()
        
        # 如果有生成的图像，返回路径
        if generated_image_path[0]:
            if progress is not None:
                progress(1.0, "图像生成完成！")
            print(f"返回生成的图像路径: {generated_image_path[0]}")
            return generated_image_path[0]
        
        # 尝试查找最新保存的图像
        print("未找到生成的图像，尝试查找最新保存的图像...")
        if progress is not None:
            progress(0.95, "未找到生成的图像，尝试查找最新保存的图像...")
        result = find_latest_image()
        if progress is not None:
            progress(1.0, "完成")
        return result
        
    except Exception as e:
        print(f"与ComfyUI接口通信错误: {str(e)}")
        import traceback
        traceback.print_exc()
        # 记录到日志文件
        logging.error(f"与ComfyUI接口通信错误: {str(e)}")
        logging.error(traceback.format_exc())
        # 更新进度 - 错误状态
        if progress is not None:
            progress(1.0, f"错误: {str(e)}")
        # 出错时尝试查找最近保存的图像
        return find_latest_image()

# 提取当前参数
params = extract_adjustable_params()

# 提取图生图可调节参数
img2img_params = extract_img2img_params()

# 尝试获取模型列表
models = get_models_list()

# 把已配置的模型添加到选项中（如果不存在）
def ensure_model_in_list(model_list, value):
    if value and value not in model_list:
        model_list.append(value)
    return model_list

# 查找最新生成的图片
def find_latest_image():
    try:
        # 从workflows.json中获取保存路径的格式
        save_path_format = ""
        if "3" in workflow and "inputs" in workflow["3"]:
            save_path_format = workflow["3"]["inputs"].get("filename_prefix", "")
        
        if not save_path_format:
            logging.warning("无法从workflow中获取保存路径格式")
            # 尝试查找ComfyUI输出目录
            comfyui_output = os.path.join(WSL_COMFYUI_PATH, "output")
            if os.path.exists(comfyui_output):
                logging.info(f"尝试在ComfyUI默认输出目录查找: {comfyui_output}")
                return find_latest_in_directory(comfyui_output)
            return None
        
        # 假设保存路径格式是文件夹/日期/时间_xx_模型名
        # 我们只需要找到文件夹部分，注意使用反斜杠
        base_folder = save_path_format.split('\\')[0] if '\\' in save_path_format else save_path_format.split('/')[0] if '/' in save_path_format else ""
        
        if not base_folder:
            logging.warning("无法从保存路径格式中提取基础文件夹")
            return None
        
        if os.path.exists(base_folder):
            logging.info(f"在目录中查找最新图像: {base_folder}")
            return find_latest_in_directory(base_folder)
        else:
            logging.warning(f"指定的保存目录不存在: {base_folder}")
            
            # 尝试在ComfyUI可能的输出路径查找
            potential_paths = [
                os.path.join(WSL_COMFYUI_PATH, "output"),
                os.path.join(WSL_COMFYUI_PATH, "output", base_folder),
                os.path.join(WSL_COMFYUI_PATH, "output"),  # 重复路径作为备份
                "output",
                base_folder
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    logging.info(f"尝试在备选路径查找: {path}")
                    result = find_latest_in_directory(path)
                    if result:
                        return result
                        
            logging.error(f"无法找到最新图像，已尝试的所有路径都不存在")
            return None
    except Exception as e:
        logging.error(f"查找最新图像时出错: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return None

# 在指定目录查找最新图像
def find_latest_in_directory(directory):
    try:
        logging.info(f"在目录中查找最新图像: {directory}")
        latest_file = None
        latest_time = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join(root, file)
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = file_path
        
        if latest_file:
            logging.info(f"找到最新图像: {latest_file}, 修改时间: {time.ctime(latest_time)}")
        else:
            logging.warning(f"在目录 {directory} 中未找到任何图像文件")
            
        return latest_file
    except Exception as e:
        logging.error(f"在目录 {directory} 中查找图像时出错: {str(e)}")
        return None

# 创建界面
# 文生图界面
with gr.Blocks(title="文生图 - ComfyUI接口") as txt2img_demo:
    gr.Markdown("# 文生图接口")
    
    with gr.Row():
        # 左侧参数控制区
        with gr.Column(scale=2):
            # 提示词部分（移动到最顶部）
            gr.Markdown("### 提示词")
            face_prompt = gr.Textbox(value=params["face_prompt"], label="面部及摄影设备", lines=2)
            clothes_prompt = gr.Textbox(value=params["clothes_prompt"], label="衣着及动作", lines=2)
            environment_prompt = gr.Textbox(value=params["environment_prompt"], label="环境", lines=3)
            
            # 模型选择部分
            gr.Markdown("### 模型选择 (已配置好，一般不需更改)")
            
            # UNET模型选择
            unet_models = ensure_model_in_list(models.get("unet", []), params.get("unet_name", ""))
            unet_model = gr.Dropdown(choices=unet_models, value=params.get("unet_name", ""), label="UNET模型", allow_custom_value=True)
            
            # CLIP模型选择
            clip_models = models.get("clip", [])
            clip_models = ensure_model_in_list(clip_models, params.get("clip_name1", ""))
            clip_models = ensure_model_in_list(clip_models, params.get("clip_name2", ""))
            with gr.Row():
                clip_model1 = gr.Dropdown(choices=clip_models, value=params.get("clip_name1", ""), label="CLIP模型1", allow_custom_value=True)
                clip_model2 = gr.Dropdown(choices=clip_models, value=params.get("clip_name2", ""), label="CLIP模型2", allow_custom_value=True)
            
            # VAE模型选择
            vae_models = ensure_model_in_list(models.get("vae", []), params.get("vae_name", ""))
            vae_model = gr.Dropdown(choices=vae_models, value=params.get("vae_name", ""), label="VAE模型", allow_custom_value=True)
            
            # LoRA 参数部分 (移到这里)
            gr.Markdown("### LoRA 设置")
            lora_models = models.get("lora", ["None"])
            lora_models = ensure_model_in_list(lora_models, params["lora_01"])
            lora_models = ensure_model_in_list(lora_models, params["lora_02"])
            lora_models = ensure_model_in_list(lora_models, params["lora_03"])
            lora_models = ensure_model_in_list(lora_models, params["lora_04"])
            
            with gr.Row():
                with gr.Column(scale=2):
                    lora_01 = gr.Dropdown(choices=lora_models, value=params["lora_01"], label="LoRA 1", allow_custom_value=True)
                with gr.Column(scale=1):
                    strength_01 = gr.Slider(minimum=0, maximum=2, step=0.01, value=params["strength_01"], label="强度 1")
            
            with gr.Row():
                with gr.Column(scale=2):
                    lora_02 = gr.Dropdown(choices=lora_models, value=params["lora_02"], label="LoRA 2", allow_custom_value=True)
                with gr.Column(scale=1):
                    strength_02 = gr.Slider(minimum=0, maximum=2, step=0.01, value=params["strength_02"], label="强度 2")
            
            with gr.Row():
                with gr.Column(scale=2):
                    lora_03 = gr.Dropdown(choices=lora_models, value=params["lora_03"], label="LoRA 3", allow_custom_value=True)
                with gr.Column(scale=1):
                    strength_03 = gr.Slider(minimum=0, maximum=2, step=0.01, value=params["strength_03"], label="强度 3")
            
            with gr.Row():
                with gr.Column(scale=2):
                    lora_04 = gr.Dropdown(choices=lora_models, value=params["lora_04"], label="LoRA 4", allow_custom_value=True)
                with gr.Column(scale=1):
                    strength_04 = gr.Slider(minimum=0, maximum=2, step=0.01, value=params["strength_04"], label="强度 4")
            
            # 基本参数部分
            gr.Markdown("### 基本参数")
            with gr.Row():
                with gr.Column(scale=1):
                    width = gr.Slider(minimum=256, maximum=2048, step=8, value=params["width"], label="宽度")
                    height = gr.Slider(minimum=256, maximum=2048, step=8, value=params["height"], label="高度")
                
                with gr.Column(scale=1):
                    sampler_options = ["euler", "euler_cfg_pp", "euler_ancestral", "euler_ancestral_cfg_pp", 
                                     "heun", "heunpp2", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", 
                                     "dpmpp_2s_ancestral", "dpmpp_2s_ancestral_cfg_pp", "dpmpp_sde", "dpmpp_sde_gpu",
                                     "dpmpp_2m", "dpmpp_2m_cfg_pp", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", 
                                     "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", "ddpm", "LCM", "ipndm", "ipndm_v", 
                                     "deis", "res_multistep", "res_multistep_cfg_pp", "res_multistep_ancestral", 
                                     "res_multistep_ancestral_cfg", "gradient_estimation", "gradient_estimation_cfg_pp",
                                     "er_sde", "seeds_2", "uni_pc", "uni_pc_bh2"]
                    sampler = gr.Dropdown(choices=sampler_options, value=params["sampler_name"], label="采样器")
                    
                    scheduler_options = ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta", "linear_quadratic", "kl_optimal"]
                    scheduler = gr.Dropdown(choices=scheduler_options, value=params["scheduler"], label="调度器")
            
            with gr.Row():
                steps = gr.Slider(minimum=1, maximum=100, step=1, value=params["steps"], label="采样步数")
                denoise = gr.Slider(minimum=0, maximum=1, step=0.01, value=params["denoise"], label="去噪强度")
                guidance = gr.Slider(minimum=1, maximum=20, step=0.1, value=params["guidance"], label="引导强度（数值越小越贴近提示词，数值越大AI自由发挥空间越大）")
            
            # 随机种子和随机生成按钮
            with gr.Row():
                noise_seed = gr.Number(value=params["noise_seed"], label="随机种子", precision=0)
                random_seed_btn = gr.Button("随机生成种子")
            
            # 生成按钮
            generate_btn = gr.Button("生成图像", variant="primary", size="lg")
        
        # 右侧图片显示区
        with gr.Column(scale=1):
            gr.Markdown("### 生成结果预览")
            
            # 添加打开output文件夹的函数
            def open_output_folder_txt2img():
                # 确保output文件夹存在
                os.makedirs("output", exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        os.system(f'explorer "{os.path.abspath("output")}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath("output")}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath("output")}"')
                    return "已打开output文件夹"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 添加状态显示区
            status_text = gr.Markdown("准备就绪")
            image_output = gr.Image(label="生成的图片", type="filepath")
            
            # 添加浏览输出文件夹按钮
            open_output_btn_txt2img = gr.Button("浏览输出文件夹")
            output_folder_status_txt2img = gr.Textbox(label="状态", visible=False)
            open_output_btn_txt2img.click(fn=open_output_folder_txt2img, inputs=[], outputs=output_folder_status_txt2img)
    
    # 进度条
    progress_bar = gr.Progress()
    
    # 收集所有参数
    all_inputs = [
        width, height, sampler, scheduler, steps, denoise, guidance, noise_seed,
        lora_01, strength_01, lora_02, strength_02, lora_03, strength_03, lora_04, strength_04,
        face_prompt, clothes_prompt, environment_prompt,
        unet_model, clip_model1, clip_model2, vae_model  # 添加模型选择参数
    ]
    
    # 生成图像按钮的点击事件
    def generate_image(*args, progress=gr.Progress()):
        updated_params = {}
        
        # 将输入参数整合到一个字典中
        updated_params["width"] = args[0]
        updated_params["height"] = args[1]
        updated_params["sampler_name"] = args[2]
        updated_params["scheduler"] = args[3]
        updated_params["steps"] = args[4]
        updated_params["denoise"] = args[5]
        updated_params["guidance"] = args[6]
        updated_params["noise_seed"] = args[7]
        updated_params["lora_01"] = args[8]
        updated_params["strength_01"] = args[9]
        updated_params["lora_02"] = args[10]
        updated_params["strength_02"] = args[11]
        updated_params["lora_03"] = args[12]
        updated_params["strength_03"] = args[13]
        updated_params["lora_04"] = args[14]
        updated_params["strength_04"] = args[15]
        updated_params["face_prompt"] = args[16]
        updated_params["clothes_prompt"] = args[17]
        updated_params["environment_prompt"] = args[18]
        updated_params["unet_name"] = args[19]
        updated_params["clip_name1"] = args[20]
        updated_params["clip_name2"] = args[21]
        updated_params["vae_name"] = args[22]
        
        # 保存参数到JSON文件
        progress(0.05, "保存参数到配置文件...")
        saved_workflow = save_workflow(updated_params)
        
        # 创建状态更新的函数
        status_text = "图像生成完成！"
        
        def progress_callback(value, message):
            nonlocal status_text
            status_text = message
            progress(value, message)
            print(f"UI进度更新: {value:.2f} - {message}")
        
        # 发送工作流到ComfyUI并获取生成结果
        result_image = send_workflow_to_comfyui(saved_workflow, progress_callback)
        
        # 返回生成的图像
        return result_image, status_text
    
    # 随机种子按钮的点击事件
    random_seed_btn.click(fn=generate_random_seed, inputs=None, outputs=noise_seed)
    
    # 生成按钮的点击事件
    generate_btn.click(
        fn=generate_image, 
        inputs=all_inputs, 
        outputs=[image_output, status_text],
        show_progress="full"
    )

# 图生图界面
with gr.Blocks(title="图生图 - ComfyUI接口") as img2img_demo:
    gr.Markdown("# 图生图接口")
    
    with gr.Row():
        # 左侧参数控制区
        with gr.Column(scale=2):
            # 输入图像上传
            gr.Markdown("### 输入图像")
            
            # 添加打开input文件夹的函数
            def open_input_folder():
                # 确保ComfyUI的input文件夹存在
                comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
                os.makedirs(comfyui_input_path, exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        # 直接使用WSL路径打开，不转换为本地路径
                        os.system(f'explorer "{comfyui_input_path}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath(comfyui_input_path)}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath(comfyui_input_path)}"')
                    return f"已打开ComfyUI的input文件夹: {comfyui_input_path}"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 修改图像上传组件，自定义保存路径
            def save_to_input_folder(img):
                if img is None:
                    return None, "未上传图片", "图片尺寸: 使用上传图片的原始尺寸", None
                    
                # 确保ComfyUI的input文件夹存在
                comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
                os.makedirs(comfyui_input_path, exist_ok=True)
                
                # 获取当前时间作为文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 构建文件路径
                if isinstance(img, str):  # 如果已经是文件路径
                    ext = os.path.splitext(img)[1].lower()
                    if not ext:
                        ext = ".png"  # 默认扩展名
                    file_path = os.path.join(comfyui_input_path, f"upload_{timestamp}{ext}")
                    
                    # 复制文件
                    shutil.copy2(img, file_path)
                    
                    # 获取图片尺寸
                    try:
                        with Image.open(file_path) as img_obj:
                            width, height = img_obj.size
                            dimension_text = f"图片尺寸: {width} x {height} 像素"
                    except Exception as e:
                        dimension_text = f"无法获取图片尺寸: {str(e)}"
                else:  # 如果是PIL图像对象
                    file_path = os.path.join(comfyui_input_path, f"upload_{timestamp}.png")
                    img.save(file_path)
                    
                    # 获取图片尺寸
                    try:
                        width, height = img.size
                        dimension_text = f"图片尺寸: {width} x {height} 像素"
                    except Exception as e:
                        dimension_text = f"无法获取图片尺寸: {str(e)}"
                
                # 获取文件名（不包含路径）
                filename = os.path.basename(file_path)
                
                print(f"已保存上传图片到ComfyUI的input文件夹: {file_path}")
                
                # 更新下拉菜单选项
                new_images = get_input_folder_images()
                dropdown_choices = []
                for name in new_images:
                    full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                    try:
                        size_kb = os.path.getsize(full_path) // 1024
                        dropdown_choices.append((f"{name} ({size_kb} KB)", full_path))
                    except Exception as e:
                        print(f"获取文件大小出错: {e}")
                
                return file_path, f"已保存图片: {file_path} (文件名: {filename})", dimension_text, gr.update(choices=dropdown_choices, value=file_path)
            
            input_image = gr.Image(label="上传图片", type="filepath")
            image_path_text = gr.Textbox(label="图片路径", interactive=False)
            image_dimensions = gr.Textbox(label="图片尺寸", interactive=False)
            
            # 获取文件夹中所有图片
            existing_images = get_input_folder_images()
            image_choices = []
            for name in existing_images:
                full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                try:
                    size_kb = os.path.getsize(full_path) // 1024
                    image_choices.append((f"{name} ({size_kb} KB)", full_path))
                except Exception as e:
                    print(f"获取文件大小出错: {e}")
                    
            # 下面是原始有错误的代码
            # image_choices = [(f"{name} ({os.path.getsize(path) // 1024} KB)", path) for name, path in existing_images]
            
            # 添加图片选择下拉菜单
            image_dropdown = gr.Dropdown(
                choices=image_choices,
                label="选择已有图片",
                info="选择已存在的图片而不是重新上传",
                type="value"
            )
            
            # 刷新图片列表按钮
            refresh_btn = gr.Button("刷新图片列表")
            
            def refresh_image_list():
                new_images = get_input_folder_images()
                new_choices = []
                for name in new_images:
                    full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                    try:
                        size_kb = os.path.getsize(full_path) // 1024
                        new_choices.append((f"{name} ({size_kb} KB)", full_path))
                    except Exception as e:
                        print(f"刷新图片列表时获取文件大小出错: {e}")
                return gr.update(choices=new_choices)
                
                # 下面是原始有错误的代码
                # return gr.update(
                #     choices=[(f"{name} ({os.path.getsize(path) // 1024} KB)", path) for name, path in new_images]
                # )
            
            refresh_btn.click(fn=refresh_image_list, inputs=[], outputs=[image_dropdown])
            
            input_image.upload(fn=save_to_input_folder, inputs=input_image, outputs=[input_image, image_path_text, image_dimensions, image_dropdown])
            
            # 下拉菜单选择图片时的处理函数
            image_dropdown.change(fn=select_existing_image, inputs=[image_dropdown], outputs=[input_image, image_path_text, image_dimensions])
            
            # 添加浏览文件夹按钮
            open_folder_btn = gr.Button("浏览图片文件夹")
            folder_status = gr.Textbox(label="状态", visible=False)
            open_folder_btn.click(fn=open_input_folder, inputs=[], outputs=folder_status)
            
            # 提示词部分
            gr.Markdown("### 提示词")
            i2i_face_prompt = gr.Textbox(value=img2img_params.get("face_prompt", ""), label="面部及摄影设备", lines=2)
            i2i_clothes_prompt = gr.Textbox(value=img2img_params.get("clothes_prompt", ""), label="衣着及动作", lines=2)
            i2i_environment_prompt = gr.Textbox(value=img2img_params.get("environment_prompt", ""), label="环境", lines=3)
            
            # 模型选择部分
            gr.Markdown("### 模型选择 (已配置好，一般不需更改)")
            
            # UNET模型选择
            i2i_unet_model = gr.Dropdown(choices=unet_models, value=img2img_params.get("unet_name", ""), label="UNET模型", allow_custom_value=True)
            
            # CLIP模型选择
            with gr.Row():
                i2i_clip_model1 = gr.Dropdown(choices=clip_models, value=img2img_params.get("clip_name1", ""), label="CLIP模型1", allow_custom_value=True)
                i2i_clip_model2 = gr.Dropdown(choices=clip_models, value=img2img_params.get("clip_name2", ""), label="CLIP模型2", allow_custom_value=True)
            
            # VAE模型选择
            i2i_vae_model = gr.Dropdown(choices=vae_models, value=img2img_params.get("vae_name", ""), label="VAE模型", allow_custom_value=True)
            
            # LoRA 参数部分
            gr.Markdown("### LoRA 设置")
            with gr.Row():
                with gr.Column(scale=2):
                    i2i_lora_01 = gr.Dropdown(choices=lora_models, value=img2img_params.get("lora_01", "None"), label="LoRA 1", allow_custom_value=True)
                with gr.Column(scale=1):
                    i2i_strength_01 = gr.Slider(minimum=0, maximum=2, step=0.01, value=img2img_params.get("strength_01", 0.8), label="强度 1")
            
            with gr.Row():
                with gr.Column(scale=2):
                    i2i_lora_02 = gr.Dropdown(choices=lora_models, value=img2img_params.get("lora_02", "None"), label="LoRA 2", allow_custom_value=True)
                with gr.Column(scale=1):
                    i2i_strength_02 = gr.Slider(minimum=0, maximum=2, step=0.01, value=img2img_params.get("strength_02", 0.8), label="强度 2")
            
            with gr.Row():
                with gr.Column(scale=2):
                    i2i_lora_03 = gr.Dropdown(choices=lora_models, value=img2img_params.get("lora_03", "None"), label="LoRA 3", allow_custom_value=True)
                with gr.Column(scale=1):
                    i2i_strength_03 = gr.Slider(minimum=0, maximum=2, step=0.01, value=img2img_params.get("strength_03", 1), label="强度 3")
            
            with gr.Row():
                with gr.Column(scale=2):
                    i2i_lora_04 = gr.Dropdown(choices=lora_models, value=img2img_params.get("lora_04", "None"), label="LoRA 4", allow_custom_value=True)
                with gr.Column(scale=1):
                    i2i_strength_04 = gr.Slider(minimum=0, maximum=2, step=0.01, value=img2img_params.get("strength_04", 1), label="强度 4")
            
            # 基本参数部分
            gr.Markdown("### 基本参数")
            with gr.Row():
                with gr.Column(scale=1):
                    # 移除宽度和高度滑动条，替换为图片尺寸显示
                    image_dimensions = gr.Textbox(value="图片尺寸: 使用上传图片的原始尺寸", label="图片尺寸", interactive=False)
                
                with gr.Column(scale=1):
                    i2i_sampler = gr.Dropdown(choices=sampler_options, value=img2img_params.get("sampler_name", "euler"), label="采样器")
                    i2i_scheduler = gr.Dropdown(choices=scheduler_options, value=img2img_params.get("scheduler", "simple"), label="调度器")
            
            with gr.Row():
                i2i_steps = gr.Slider(minimum=1, maximum=100, step=1, value=img2img_params.get("steps", 20), label="采样步数")
                i2i_guidance = gr.Slider(minimum=1, maximum=20, step=0.1, value=img2img_params.get("guidance", 3.5), label="引导强度")
            
            # 添加图生图重绘幅度滑动条
            i2i_redraw_strength = gr.Slider(minimum=0, maximum=1, step=0.01, value=img2img_params.get("redraw_strength", 0.75), label="图生图重绘幅度")
            
            # 随机种子和随机生成按钮
            with gr.Row():
                i2i_noise_seed = gr.Number(value=img2img_params.get("noise_seed", 0), label="随机种子", precision=0)
                i2i_random_seed_btn = gr.Button("随机生成种子")
            
            # 生成按钮
            i2i_generate_btn = gr.Button("生成图像", variant="primary", size="lg")
        
        # 右侧图片显示区
        with gr.Column(scale=1):
            gr.Markdown("### 生成结果预览")
            
            # 添加打开output文件夹的函数
            def open_output_folder():
                # 确保output文件夹存在
                os.makedirs("output", exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        os.system(f'explorer "{os.path.abspath("output")}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath("output")}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath("output")}"')
                    return "已打开output文件夹"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 添加状态显示区
            i2i_status_text = gr.Markdown("准备就绪")
            i2i_image_output = gr.Image(label="生成的图片", type="filepath")
            
            # 添加浏览输出文件夹按钮
            open_output_btn = gr.Button("浏览输出文件夹")
            output_folder_status = gr.Textbox(label="状态", visible=False)
            open_output_btn.click(fn=open_output_folder, inputs=[], outputs=output_folder_status)
    
    # 进度条
    i2i_progress_bar = gr.Progress()
    
    # 收集所有参数
    i2i_all_inputs = [
        input_image,  # 添加输入图像
        i2i_sampler, i2i_scheduler, i2i_steps, i2i_guidance, i2i_noise_seed,
        i2i_lora_01, i2i_strength_01, i2i_lora_02, i2i_strength_02, i2i_lora_03, i2i_strength_03, i2i_lora_04, i2i_strength_04,
        i2i_face_prompt, i2i_clothes_prompt, i2i_environment_prompt,
        i2i_unet_model, i2i_clip_model1, i2i_clip_model2, i2i_vae_model,
        image_path_text,  # 添加图片路径文本框
        image_dimensions,  # 添加图片尺寸文本框
        i2i_redraw_strength  # 添加图生图重绘幅度滑动条
    ]
    
    # 图生图生成函数
    def generate_img2img(*args, progress=gr.Progress()):
        input_image_path = args[0]
        # 由于删除了宽高参数和去噪强度参数，需要调整索引
        sampler_name = args[1]
        scheduler = args[2]
        steps = args[3]
        guidance = args[4]
        noise_seed = args[5]
        lora_01 = args[6]
        strength_01 = args[7]
        lora_02 = args[8]
        strength_02 = args[9]
        lora_03 = args[10]
        strength_03 = args[11]
        lora_04 = args[12]
        strength_04 = args[13]
        face_prompt = args[14]
        clothes_prompt = args[15]
        environment_prompt = args[16]
        unet_name = args[17]
        clip_name1 = args[18]
        clip_name2 = args[19]
        vae_name = args[20]
        image_path_text = args[21]  # 获取图片路径文本框的值
        image_dimensions_text = args[22]  # 获取图片尺寸文本框的值
        i2i_redraw_strength = args[23]  # 获取图生图重绘幅度参数
        
        # 优先使用文本框中的图片路径（如果有）
        if image_path_text and (image_path_text.startswith("已保存图片:") or image_path_text.startswith("已选择图片:")):
            saved_path = image_path_text.replace("已保存图片:", "").replace("已选择图片:", "").strip()
            if os.path.exists(saved_path):
                input_image_path = saved_path
                print(f"使用文本框中的图片路径: {input_image_path}")
        
        if not input_image_path:
            return None, "错误：请先上传或选择输入图像"
        
        # 确保input_image_path是一个有效的文件路径
        if not os.path.exists(input_image_path):
            return None, f"错误：输入图像路径无效 - {input_image_path}"
        
        # 打印使用的输入图像
        print(f"使用输入图像: {input_image_path}")
        
        # 从图像获取宽高
        try:
            with Image.open(input_image_path) as img:
                width, height = img.size
                print(f"获取到图片尺寸: {width} x {height}")
        except Exception as e:
            print(f"获取图片尺寸失败: {e}")
            width, height = 512, 512  # 使用默认值
        
        updated_params = {}
        
        # 将输入参数整合到一个字典中
        updated_params["width"] = width
        updated_params["height"] = height
        updated_params["sampler_name"] = sampler_name
        updated_params["scheduler"] = scheduler
        updated_params["steps"] = steps
        # 移除去噪强度参数，使用重绘幅度替代
        updated_params["guidance"] = guidance
        updated_params["noise_seed"] = noise_seed
        updated_params["lora_01"] = lora_01
        updated_params["strength_01"] = strength_01
        updated_params["lora_02"] = lora_02
        updated_params["strength_02"] = strength_02
        updated_params["lora_03"] = lora_03
        updated_params["strength_03"] = strength_03
        updated_params["lora_04"] = lora_04
        updated_params["strength_04"] = strength_04
        updated_params["face_prompt"] = face_prompt
        updated_params["clothes_prompt"] = clothes_prompt
        updated_params["environment_prompt"] = environment_prompt
        updated_params["unet_name"] = unet_name
        updated_params["clip_name1"] = clip_name1
        updated_params["clip_name2"] = clip_name2
        updated_params["vae_name"] = vae_name
        updated_params["redraw_strength"] = i2i_redraw_strength  # 图生图重绘幅度参数
        
        # 保存参数到JSON文件
        progress(0.05, "保存参数到配置文件...")
        saved_workflow = save_img2img_workflow(updated_params)
        
        # 创建状态更新的函数
        status_text = "图像生成完成！"
        
        def progress_callback(value, message):
            nonlocal status_text
            status_text = message
            progress(value, message)
            print(f"UI进度更新: {value:.2f} - {message}")
        
        # 发送工作流到ComfyUI并获取生成结果
        try:
            result_image = send_img2img_workflow_to_comfyui(saved_workflow, input_image_path, progress_callback)
            
            # 如果生成成功，显示成功信息
            if result_image and os.path.exists(result_image):
                return result_image, "图像生成完成！"
            else:
                return None, "图像生成失败，未能获取结果图像"
        except Exception as e:
            import traceback
            error_msg = f"处理过程中出错: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return None, error_msg
    
    # 随机种子按钮的点击事件
    i2i_random_seed_btn.click(fn=generate_random_seed, inputs=None, outputs=i2i_noise_seed)
    
    # 生成按钮的点击事件
    i2i_generate_btn.click(
        fn=generate_img2img, 
        inputs=i2i_all_inputs, 
        outputs=[i2i_image_output, i2i_status_text],
        show_progress="full"
    )

# 读取三视图工作流文件
def load_random_three_views_workflow():
    # 首先尝试当前目录的workflows文件夹
    try:
        with open("workflows/Random_three_views.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Random_three_views.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到Random_three_views.json文件，已尝试路径: workflows/Random_three_views.json 和 {workflow_path}")
            raise

# 保存三视图工作流文件
def save_random_three_views_workflow_json(workflow_data):
    # 首先尝试当前目录的workflows文件夹
    try:
        os.makedirs("workflows", exist_ok=True)
        with open("workflows/Random_three_views.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Random_three_views.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 加载三视图工作流
try:
    random_three_views_workflow = load_random_three_views_workflow()
    # 检查303节点
    if "303" in random_three_views_workflow:
        if "inputs" in random_three_views_workflow["303"] and "text" in random_three_views_workflow["303"]["inputs"]:
            default_image_name = random_three_views_workflow["303"]["inputs"]["text"]
            print(f"加载时发现303节点默认图片名称: '{default_image_name}'")
        else:
            print(f"警告：303节点结构不完整: {random_three_views_workflow['303']}")
    else:
        print("警告：未找到303节点")
except Exception as e:
    logging.error(f"加载三视图工作流失败: {e}")
    random_three_views_workflow = {}  # 使用空字典作为默认值

# 提取三视图可调节参数
def extract_random_three_views_params():
    params = {
        # 设置所有可能需要的参数的默认值，确保即使工作流结构不同也能正常运行
        "width": 1280,  # 默认值修改为1280
        "height": 1280, # 默认值修改为1280
        "sampler_name": "euler",
        "scheduler": "simple",
        "steps": 20,
        "denoise": 1,
        "guidance": 3.5,
        "noise_seed": 0,
        "lora_01": "None",
        "strength_01": 0.8,
        "lora_02": "None",
        "strength_02": 0.8,
        "lora_03": "None",
        "strength_03": 1,
        "lora_04": "None",
        "strength_04": 1,
        "prompt": "",  # 替换为单一提示词参数
        "unet_name": "FLUX/flux-dev.safetensors",
        "clip_name1": "flux/t5xxl_fp16.safetensors",
        "clip_name2": "flux/clip_l.safetensors",
        "vae_name": "flux/ae.safetensors",
        "controlnet_name": "flux/Shakker-Labs/diffusion_pytorch_model.safetensors", # 添加ControlNet模型默认路径
        "image_name": "character_sheet_flux",  # 提供正确的默认值
        "pose_image": None  # 添加姿势图参数
    }
    
    # 如果工作流为空，直接返回默认参数
    if not random_three_views_workflow:
        print("三视图工作流为空，使用默认参数")
        return params
    
    # 打印工作流的节点ID，帮助调试
    print(f"三视图工作流节点ID: {list(random_three_views_workflow.keys())}")
    
    # 直接输出25节点的完整内容，帮助调试
    if "25" in random_three_views_workflow:
        print(f"节点25的完整内容: {json.dumps(random_three_views_workflow['25'], ensure_ascii=False, indent=2)}")
    
    # 检查10节点（姿势图）
    if "10" in random_three_views_workflow:
        print(f"节点10存在，开始提取姿势图参数")
    
    try:
        # 提取25节点参数（图片命名）- 优先提取这个节点数据并打印出来
        if "25" in random_three_views_workflow:
            if "inputs" in random_three_views_workflow["25"] and "string" in random_three_views_workflow["25"]["inputs"]:
                params["image_name"] = random_three_views_workflow["25"]["inputs"]["string"]
                print(f"成功从节点25提取图片名称: '{params['image_name']}'")
            else:
                print("节点25存在，但没有inputs.string字段")
                # 如果节点存在但没有string字段，检查其他可能的字段
                if "inputs" in random_three_views_workflow["25"]:
                    print(f"节点25的inputs字段包含: {list(random_three_views_workflow['25']['inputs'].keys())}")
                    # 检查其他可能包含名称的字段
                    for key, value in random_three_views_workflow["25"]["inputs"].items():
                        print(f"节点25的字段 {key}: {value}")
                        if isinstance(value, str) and value:
                            params["image_name"] = value
                            print(f"从字段 {key} 中找到可能的图片名称: '{value}'")
                else:
                    print(f"节点25的结构: {random_three_views_workflow['25']}")
        else:
            print("工作流中不存在节点25，使用默认值")
        
        # 提取10节点参数（姿势图）
        if "10" in random_three_views_workflow and "inputs" in random_three_views_workflow["10"]:
            if "image" in random_three_views_workflow["10"]["inputs"]:
                pose_image = random_three_views_workflow["10"]["inputs"]["image"]
                print(f"从节点10提取姿势图: {pose_image}")
                params["pose_image"] = pose_image
        
        # 提取18节点参数（提示词）
        if "18" in random_three_views_workflow and "inputs" in random_three_views_workflow["18"]:
            if "text" in random_three_views_workflow["18"]["inputs"]:
                params["prompt"] = random_three_views_workflow["18"]["inputs"]["text"]
                print(f"从节点18提取提示词: {params['prompt'][:30]}..." if len(params["prompt"]) > 30 else f"从节点18提取提示词: {params['prompt']}")
        
        # 提取图像尺寸参数 - 从21、23、24节点提取
        if "21" in random_three_views_workflow and "inputs" in random_three_views_workflow["21"]:
            if "width" in random_three_views_workflow["21"]["inputs"] and "height" in random_three_views_workflow["21"]["inputs"]:
                params["width"] = random_three_views_workflow["21"]["inputs"].get("width", 1280)
                params["height"] = random_three_views_workflow["21"]["inputs"].get("height", 1280)
                print(f"从节点21提取图像尺寸: {params['width']}x{params['height']}")
        # 如果21节点不存在尺寸信息，尝试从23节点提取
        elif "23" in random_three_views_workflow and "inputs" in random_three_views_workflow["23"]:
            if "width" in random_three_views_workflow["23"]["inputs"] and "height" in random_three_views_workflow["23"]["inputs"]:
                params["width"] = random_three_views_workflow["23"]["inputs"].get("width", 1280)
                params["height"] = random_three_views_workflow["23"]["inputs"].get("height", 1280)
                print(f"从节点23提取图像尺寸: {params['width']}x{params['height']}")
        # 如果23节点不存在尺寸信息，尝试从24节点提取
        elif "24" in random_three_views_workflow and "inputs" in random_three_views_workflow["24"]:
            if "width" in random_three_views_workflow["24"]["inputs"] and "height" in random_three_views_workflow["24"]["inputs"]:
                params["width"] = random_three_views_workflow["24"]["inputs"].get("width", 1280)
                params["height"] = random_three_views_workflow["24"]["inputs"].get("height", 1280)
                print(f"从节点24提取图像尺寸: {params['width']}x{params['height']}")
        
        # 确保宽高相等（方形图）且在有效范围内
        if params["width"] != params["height"]:
            # 如果不相等，使用较大的值
            size = max(params["width"], params["height"])
            # 确保在有效范围内
            size = max(1280, min(size, 2048))
            params["width"] = size
            params["height"] = size
            print(f"调整图像尺寸为方形: {size}x{size}")
        
        # 提取12节点参数（ControlNet模型）
        if "12" in random_three_views_workflow and "inputs" in random_three_views_workflow["12"]:
            if "control_net_name" in random_three_views_workflow["12"]["inputs"]:
                params["controlnet_name"] = random_three_views_workflow["12"]["inputs"]["control_net_name"]
                print(f"从节点12提取ControlNet模型: {params['controlnet_name']}")
        
        # 更新提取UNET模型 - 使用13号节点
        if "13" in random_three_views_workflow and "inputs" in random_three_views_workflow["13"]:
            if "unet_name" in random_three_views_workflow["13"]["inputs"]:
                params["unet_name"] = random_three_views_workflow["13"]["inputs"]["unet_name"]
                print(f"从节点13提取UNET模型: {params['unet_name']}")
        
        # 更新提取CLIP模型 - 使用14号节点
        if "14" in random_three_views_workflow and "inputs" in random_three_views_workflow["14"]:
            if "clip_name1" in random_three_views_workflow["14"]["inputs"]:
                params["clip_name1"] = random_three_views_workflow["14"]["inputs"]["clip_name1"]
            if "clip_name2" in random_three_views_workflow["14"]["inputs"]:
                params["clip_name2"] = random_three_views_workflow["14"]["inputs"]["clip_name2"]
            print(f"从节点14提取CLIP模型")
        
        # 更新提取VAE模型 - 使用15号节点
        if "15" in random_three_views_workflow and "inputs" in random_three_views_workflow["15"]:
            if "vae_name" in random_three_views_workflow["15"]["inputs"]:
                params["vae_name"] = random_three_views_workflow["15"]["inputs"]["vae_name"]
                print(f"从节点15提取VAE模型: {params['vae_name']}")
        
        # 更新提取LoRA参数 - 使用17号节点
        if "17" in random_three_views_workflow and "inputs" in random_three_views_workflow["17"]:
            for lora_key in ["lora_01", "lora_02", "lora_03", "lora_04"]:
                if lora_key in random_three_views_workflow["17"]["inputs"]:
                    params[lora_key] = random_three_views_workflow["17"]["inputs"][lora_key]
            for strength_key in ["strength_01", "strength_02", "strength_03", "strength_04"]:
                if strength_key in random_three_views_workflow["17"]["inputs"]:
                    params[strength_key] = random_three_views_workflow["17"]["inputs"][strength_key]
            print(f"从节点17提取LoRA参数")
        
        # 提取采样器参数 - 适配不同节点ID
        for node_id in ["3"]:  # 更新采样器节点ID
            if node_id in random_three_views_workflow and "inputs" in random_three_views_workflow[node_id]:
                if "sampler_name" in random_three_views_workflow[node_id]["inputs"]:
                    params["sampler_name"] = random_three_views_workflow[node_id]["inputs"]["sampler_name"]
                    print(f"从节点 {node_id} 提取采样器: {params['sampler_name']}")
                    break
        
        # 提取调度器参数 - 适配不同节点ID
        for node_id in ["2"]:  # 更新调度器节点ID
            if node_id in random_three_views_workflow and "inputs" in random_three_views_workflow[node_id]:
                if "scheduler" in random_three_views_workflow[node_id]["inputs"]:
                    params["scheduler"] = random_three_views_workflow[node_id]["inputs"]["scheduler"]
                if "steps" in random_three_views_workflow[node_id]["inputs"]:
                    params["steps"] = random_three_views_workflow[node_id]["inputs"]["steps"]
                if "denoise" in random_three_views_workflow[node_id]["inputs"]:
                    params["denoise"] = random_three_views_workflow[node_id]["inputs"]["denoise"]
                print(f"从节点 {node_id} 提取调度器参数")
                break
        
        # 提取随机噪声种子 - 适配不同节点ID
        for node_id in ["16"]:  # 更新随机种子节点ID
            if node_id in random_three_views_workflow and "inputs" in random_three_views_workflow[node_id]:
                if "noise_seed" in random_three_views_workflow[node_id]["inputs"]:
                    params["noise_seed"] = random_three_views_workflow[node_id]["inputs"]["noise_seed"]
                    print(f"从节点 {node_id} 提取随机种子: {params['noise_seed']}")
                    break
        
        # 提取引导参数 - 适配不同节点ID
        for node_id in ["8"]:  # 更新引导参数节点ID
            if node_id in random_three_views_workflow and "inputs" in random_three_views_workflow[node_id]:
                if "guidance" in random_three_views_workflow[node_id]["inputs"]:
                    params["guidance"] = random_three_views_workflow[node_id]["inputs"]["guidance"]
                    print(f"从节点 {node_id} 提取引导参数: {params['guidance']}")
                    break
    
    except Exception as e:
        print(f"提取三视图参数时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"三视图参数提取完成，图片名称: '{params['image_name']}'，姿势图: {params['pose_image']}")
    return params

# 保存三视图调整后的参数
def save_random_three_views_workflow(params):
    workflow_copy = copy.deepcopy(random_three_views_workflow)
    
    # 如果工作流为空，使用默认结构
    if not workflow_copy:
        logging.warning("三视图工作流为空，无法保存参数")
        return workflow_copy
    
    # 确保宽高相等（方形图）且在有效范围内
    size = max(512, min(params["width"], 2048))
    params["width"] = size
    params["height"] = size
    
    # 更新25节点参数（图片命名）
    if "25" in workflow_copy:
        if "inputs" not in workflow_copy["25"]:
            workflow_copy["25"]["inputs"] = {}
        if "string" in workflow_copy["25"]["inputs"]:
            workflow_copy["25"]["inputs"]["string"] = params["image_name"]
            print(f"已将图片名称 '{params['image_name']}' 保存到三视图工作流25号节点的string字段")
        else:
            workflow_copy["25"]["inputs"]["string"] = params["image_name"]
            print(f"已将图片名称 '{params['image_name']}' 保存到三视图工作流25号节点")
    else:
        print(f"警告：工作流中不存在25节点，无法保存图片名称 '{params['image_name']}'")
        # 尝试创建25节点
        try:
            workflow_copy["25"] = {
                "inputs": {
                    "string": params["image_name"]
                },
                "class_type": "Simple String"  # 正确的类型
            }
            print(f"已创建25节点并设置图片名称为 '{params['image_name']}'")
        except Exception as e:
            print(f"创建25节点失败: {e}")
    
    # 更新10节点参数（姿势图）
    if params.get("pose_image") and "10" in workflow_copy:
        if "inputs" not in workflow_copy["10"]:
            workflow_copy["10"]["inputs"] = {}
        workflow_copy["10"]["inputs"]["image"] = params["pose_image"]
        print(f"已将姿势图 {params['pose_image']} 保存到三视图工作流10号节点")
    
    # 更新18节点参数（提示词）
    if "18" in workflow_copy:
        if "inputs" not in workflow_copy["18"]:
            workflow_copy["18"]["inputs"] = {}
        workflow_copy["18"]["inputs"]["text"] = params["prompt"]
        print(f"已将提示词保存到三视图工作流18号节点")
    else:
        print(f"警告：工作流中不存在18号节点，无法保存提示词")
        # 尝试创建18节点
        try:
            workflow_copy["18"] = {
                "inputs": {
                    "text": params["prompt"],
                    "clip": ["17", 1]
                },
                "class_type": "CLIPTextEncode"  # 提示词节点的正确类型
            }
            print(f"已创建18节点并设置提示词")
        except Exception as e:
            print(f"创建18节点失败: {e}")
    
    # 更新12节点参数（ControlNet模型）
    if "12" in workflow_copy:
        if "inputs" not in workflow_copy["12"]:
            workflow_copy["12"]["inputs"] = {}
        workflow_copy["12"]["inputs"]["control_net_name"] = params.get("controlnet_name", "flux/Shakker-Labs/diffusion_pytorch_model.safetensors")
        print(f"已将ControlNet模型 {params.get('controlnet_name')} 保存到三视图工作流12号节点")
    else:
        print(f"警告：工作流中不存在12号节点，无法保存ControlNet模型")
    
    # 更新图像尺寸到多个节点
    # 更新21节点的尺寸参数
    if "21" in workflow_copy:
        if "inputs" not in workflow_copy["21"]:
            workflow_copy["21"]["inputs"] = {}
        workflow_copy["21"]["inputs"]["width"] = size
        workflow_copy["21"]["inputs"]["height"] = size
        print(f"已将尺寸 {size}x{size} 保存到三视图工作流21号节点")
    
    # 更新23节点的尺寸参数
    if "23" in workflow_copy:
        if "inputs" not in workflow_copy["23"]:
            workflow_copy["23"]["inputs"] = {}
        workflow_copy["23"]["inputs"]["width"] = size
        workflow_copy["23"]["inputs"]["height"] = size
        print(f"已将尺寸 {size}x{size} 保存到三视图工作流23号节点")
    
    # 更新24节点的尺寸参数
    if "24" in workflow_copy:
        if "inputs" not in workflow_copy["24"]:
            workflow_copy["24"]["inputs"] = {}
        workflow_copy["24"]["inputs"]["width"] = size
        workflow_copy["24"]["inputs"]["height"] = size
        print(f"已将尺寸 {size}x{size} 保存到三视图工作流24号节点")
    
    # 更新采样器
    if "3" in workflow_copy:  # 更新为3号节点
        workflow_copy["3"]["inputs"]["sampler_name"] = params["sampler_name"]
        print(f"已将采样器 {params['sampler_name']} 保存到三视图工作流3号节点")
    
    # 更新调度器
    if "2" in workflow_copy:  # 更新为2号节点
        workflow_copy["2"]["inputs"]["scheduler"] = params["scheduler"]
        workflow_copy["2"]["inputs"]["steps"] = params["steps"]
        workflow_copy["2"]["inputs"]["denoise"] = params["denoise"]
        print(f"已将调度器参数保存到三视图工作流2号节点")
    
    # 更新随机噪声种子
    if "16" in workflow_copy:  # 更新为16号节点
        workflow_copy["16"]["inputs"]["noise_seed"] = params["noise_seed"]
        print(f"已将随机种子 {params['noise_seed']} 保存到三视图工作流16号节点")
    
    # 更新引导参数
    if "8" in workflow_copy:  # 更新为8号节点
        workflow_copy["8"]["inputs"]["guidance"] = params["guidance"]
        print(f"已将引导参数 {params['guidance']} 保存到三视图工作流8号节点")
    
    # 更新UNET模型参数 - 使用13号节点
    if "13" in workflow_copy:
        workflow_copy["13"]["inputs"]["unet_name"] = params["unet_name"]
        print(f"已将UNET模型 {params['unet_name']} 保存到三视图工作流13号节点")
    
    # 更新CLIP模型参数 - 使用14号节点
    if "14" in workflow_copy:
        if "clip_name1" in params:
            workflow_copy["14"]["inputs"]["clip_name1"] = params["clip_name1"]
        if "clip_name2" in params:
            workflow_copy["14"]["inputs"]["clip_name2"] = params["clip_name2"]
        print(f"已将CLIP模型保存到三视图工作流14号节点")
    
    # 更新VAE模型参数 - 使用15号节点
    if "15" in workflow_copy and "vae_name" in params:
        workflow_copy["15"]["inputs"]["vae_name"] = params["vae_name"]
        print(f"已将VAE模型 {params['vae_name']} 保存到三视图工作流15号节点")
    
    # 更新LoRA参数 - 使用17号节点
    if "17" in workflow_copy:
        workflow_copy["17"]["inputs"]["lora_01"] = params["lora_01"]
        workflow_copy["17"]["inputs"]["strength_01"] = params["strength_01"]
        workflow_copy["17"]["inputs"]["lora_02"] = params["lora_02"]
        workflow_copy["17"]["inputs"]["strength_02"] = params["strength_02"]
        workflow_copy["17"]["inputs"]["lora_03"] = params["lora_03"]
        workflow_copy["17"]["inputs"]["strength_03"] = params["strength_03"]
        workflow_copy["17"]["inputs"]["lora_04"] = params["lora_04"]
        workflow_copy["17"]["inputs"]["strength_04"] = params["strength_04"]
        print(f"已将LoRA参数保存到三视图工作流17号节点")
    
    # 保存工作流
    save_random_three_views_workflow_json(workflow_copy)
    return workflow_copy

# 提取三视图参数
random_three_views_params = extract_random_three_views_params()

# 三视图界面
with gr.Blocks(title="三视图 - ComfyUI接口") as random_three_views_demo:
    gr.Markdown("# 三视图接口")
    
    # 确保先提取参数
    rtv_params = extract_random_three_views_params()
    print(f"界面初始化时的图片名称: '{rtv_params.get('image_name', '')}'")
    
    with gr.Row():
        # 左侧参数控制区
        with gr.Column(scale=2):
            # 添加"给图片取过名字呗"功能（放在最顶部）
            gr.Markdown("### 给图片取过名字呗")
            rtv_image_name = gr.Textbox(
                value=rtv_params.get("image_name", ""), 
                label="输入图片名称", 
                lines=1,
                placeholder="请输入图片名称..."
            )
            
            # 添加"上传姿势图"功能
            gr.Markdown("### 上传姿势图")
            
            # 参考图生图界面的图片上传功能
            def save_pose_image_to_input_folder(img):
                if img is None:
                    return None, "未上传图片", "图片尺寸: 未知", None
                    
                # 确保ComfyUI的input文件夹存在
                comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
                os.makedirs(comfyui_input_path, exist_ok=True)
                
                # 获取当前时间作为文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 构建文件路径
                if isinstance(img, str):  # 如果已经是文件路径
                    ext = os.path.splitext(img)[1].lower()
                    if not ext:
                        ext = ".png"  # 默认扩展名
                    file_path = os.path.join(comfyui_input_path, f"pose_{timestamp}{ext}")
                    
                    # 复制文件
                    shutil.copy2(img, file_path)
                    
                    # 获取图片尺寸
                    try:
                        with Image.open(file_path) as img_obj:
                            width, height = img_obj.size
                            dimension_text = f"图片尺寸: {width} x {height} 像素"
                    except Exception as e:
                        dimension_text = f"无法获取图片尺寸: {str(e)}"
                else:  # 如果是PIL图像对象
                    file_path = os.path.join(comfyui_input_path, f"pose_{timestamp}.png")
                    img.save(file_path)
                    
                    # 获取图片尺寸
                    try:
                        width, height = img.size
                        dimension_text = f"图片尺寸: {width} x {height} 像素"
                    except Exception as e:
                        dimension_text = f"无法获取图片尺寸: {str(e)}"
                
                # 获取文件名（不包含路径）
                filename = os.path.basename(file_path)
                
                print(f"已保存姿势图到ComfyUI的input文件夹: {file_path}")
                
                # 更新下拉菜单选项
                new_images = get_input_folder_images()
                dropdown_choices = []
                for name in new_images:
                    full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                    try:
                        size_kb = os.path.getsize(full_path) // 1024
                        dropdown_choices.append((f"{name} ({size_kb} KB)", full_path))
                    except Exception as e:
                        print(f"获取文件大小出错: {e}")
                
                return file_path, f"已保存姿势图: {file_path} (文件名: {filename})", dimension_text, gr.update(choices=dropdown_choices, value=file_path)
            
            # 打开input文件夹的函数
            def open_pose_input_folder():
                # 确保ComfyUI的input文件夹存在
                comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
                os.makedirs(comfyui_input_path, exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        # 直接使用WSL路径打开，不转换为本地路径
                        os.system(f'explorer "{comfyui_input_path}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath(comfyui_input_path)}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath(comfyui_input_path)}"')
                    return f"已打开ComfyUI的input文件夹: {comfyui_input_path}"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 选择现有图片的函数
            def select_existing_pose_image(file_path):
                if not file_path or not os.path.exists(file_path):
                    return None, "未选择图片", "图片尺寸: 未知"
                
                # 获取图片尺寸
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        dimension_text = f"图片尺寸: {width} x {height} 像素"
                except Exception as e:
                    dimension_text = f"无法获取图片尺寸: {str(e)}"
                
                return file_path, f"已选择姿势图: {file_path}", dimension_text
            
            # 图片上传组件
            rtv_pose_image = gr.Image(label="上传姿势图", type="filepath")
            rtv_pose_path_text = gr.Textbox(label="姿势图路径", interactive=False)
            rtv_pose_dimensions = gr.Textbox(label="姿势图尺寸", interactive=False)
            
            # 获取文件夹中所有图片
            existing_images = get_input_folder_images()
            image_choices = []
            for name in existing_images:
                full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                try:
                    size_kb = os.path.getsize(full_path) // 1024
                    image_choices.append((f"{name} ({size_kb} KB)", full_path))
                except Exception as e:
                    print(f"获取文件大小出错: {e}")
                    
            # 下面是原始有错误的代码
            # image_choices = [(f"{name} ({os.path.getsize(path) // 1024} KB)", path) for name, path in existing_images]
            
            # 添加图片选择下拉菜单
            rtv_pose_dropdown = gr.Dropdown(
                choices=image_choices,
                label="选择已有姿势图",
                info="选择已存在的图片而不是重新上传",
                type="value"
            )
            
            # 刷新图片列表按钮
            rtv_refresh_btn = gr.Button("刷新图片列表")
            
            def refresh_image_list():
                new_images = get_input_folder_images()
                new_choices = []
                for name in new_images:
                    full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                    try:
                        size_kb = os.path.getsize(full_path) // 1024
                        new_choices.append((f"{name} ({size_kb} KB)", full_path))
                    except Exception as e:
                        print(f"刷新图片列表时获取文件大小出错: {e}")
                return gr.update(choices=new_choices)
                
                # 下面是原始有错误的代码
                # return gr.update(
                #     choices=[(f"{name} ({os.path.getsize(path) // 1024} KB)", path) for name, path in new_images]
                # )
            
            rtv_refresh_btn.click(fn=refresh_image_list, inputs=[], outputs=[rtv_pose_dropdown])
            
            # 图片上传处理
            rtv_pose_image.upload(
                fn=save_pose_image_to_input_folder, 
                inputs=rtv_pose_image, 
                outputs=[rtv_pose_image, rtv_pose_path_text, rtv_pose_dimensions, rtv_pose_dropdown]
            )
            
            # 下拉菜单选择图片事件
            rtv_pose_dropdown.change(
                fn=select_existing_pose_image, 
                inputs=[rtv_pose_dropdown], 
                outputs=[rtv_pose_image, rtv_pose_path_text, rtv_pose_dimensions]
            )
            
            # 添加浏览文件夹按钮
            rtv_open_folder_btn = gr.Button("浏览姿势图文件夹")
            rtv_folder_status = gr.Textbox(label="状态", visible=False)
            rtv_open_folder_btn.click(fn=open_pose_input_folder, inputs=[], outputs=rtv_folder_status)
            
            # 提示词部分 - 修改为只有一个提示词输入框
            gr.Markdown("### 提示词")
            rtv_prompt = gr.Textbox(value=rtv_params.get("prompt", ""), label="只适合英文提示词", lines=3)
            
            # 模型选择部分
            gr.Markdown("### 模型选择 (已配置好，一般不需更改)")
            
            # UNET模型选择
            unet_models = ensure_model_in_list(models.get("unet", []), rtv_params.get("unet_name", ""))
            rtv_unet_model = gr.Dropdown(choices=unet_models, value=rtv_params.get("unet_name", ""), label="UNET模型", allow_custom_value=True)
            
            # CLIP模型选择
            clip_models = models.get("clip", [])
            clip_models = ensure_model_in_list(clip_models, rtv_params.get("clip_name1", ""))
            clip_models = ensure_model_in_list(clip_models, rtv_params.get("clip_name2", ""))
            with gr.Row():
                rtv_clip_model1 = gr.Dropdown(choices=clip_models, value=rtv_params.get("clip_name1", ""), label="CLIP模型1", allow_custom_value=True)
                rtv_clip_model2 = gr.Dropdown(choices=clip_models, value=rtv_params.get("clip_name2", ""), label="CLIP模型2", allow_custom_value=True)
            
            # VAE模型选择
            vae_models = ensure_model_in_list(models.get("vae", []), rtv_params.get("vae_name", ""))
            rtv_vae_model = gr.Dropdown(choices=vae_models, value=rtv_params.get("vae_name", ""), label="VAE模型", allow_custom_value=True)
            
            # ControlNet模型选择
            controlnet_models = models.get("controlnet", [])
            # 确保存在默认的ControlNet模型
            default_controlnet = "flux/Shakker-Labs/diffusion_pytorch_model.safetensors"
            controlnet_models = ensure_model_in_list(controlnet_models, rtv_params.get("controlnet_name", default_controlnet))
            rtv_controlnet_model = gr.Dropdown(choices=controlnet_models, value=rtv_params.get("controlnet_name", default_controlnet), label="ControlNet模型", allow_custom_value=True)
            
            # LoRA 参数部分
            gr.Markdown("### LoRA 设置")
            lora_models = models.get("lora", ["None"])
            lora_models = ensure_model_in_list(lora_models, rtv_params["lora_01"])
            lora_models = ensure_model_in_list(lora_models, rtv_params["lora_02"])
            lora_models = ensure_model_in_list(lora_models, rtv_params["lora_03"])
            lora_models = ensure_model_in_list(lora_models, rtv_params["lora_04"])
            
            with gr.Row():
                with gr.Column(scale=2):
                    rtv_lora_01 = gr.Dropdown(choices=lora_models, value=rtv_params["lora_01"], label="LoRA 1", allow_custom_value=True)
                with gr.Column(scale=1):
                    rtv_strength_01 = gr.Slider(minimum=0, maximum=2, step=0.01, value=rtv_params["strength_01"], label="强度 1")
            
            with gr.Row():
                with gr.Column(scale=2):
                    rtv_lora_02 = gr.Dropdown(choices=lora_models, value=rtv_params["lora_02"], label="LoRA 2", allow_custom_value=True)
                with gr.Column(scale=1):
                    rtv_strength_02 = gr.Slider(minimum=0, maximum=2, step=0.01, value=rtv_params["strength_02"], label="强度 2")
            
            with gr.Row():
                with gr.Column(scale=2):
                    rtv_lora_03 = gr.Dropdown(choices=lora_models, value=rtv_params["lora_03"], label="LoRA 3", allow_custom_value=True)
                with gr.Column(scale=1):
                    rtv_strength_03 = gr.Slider(minimum=0, maximum=2, step=0.01, value=rtv_params["strength_03"], label="强度 3")
            
            with gr.Row():
                with gr.Column(scale=2):
                    rtv_lora_04 = gr.Dropdown(choices=lora_models, value=rtv_params["lora_04"], label="LoRA 4", allow_custom_value=True)
                with gr.Column(scale=1):
                    rtv_strength_04 = gr.Slider(minimum=0, maximum=2, step=0.01, value=rtv_params["strength_04"], label="强度 4")
            
            # 基本参数部分
            gr.Markdown("### 基本参数")
            with gr.Row():
                with gr.Column(scale=1):
                    # 修改宽高滑动条，实现同步变化
                    def update_dimensions(value):
                        # 确保值在合法范围内且为整数
                        value = int(max(512, min(value, 2048)))
                        # 返回同样的值用于同步宽度和高度
                        return value, value
                    
                    # 宽度和高度使用同一个滑动条控制
                    rtv_size = gr.Slider(minimum=512, maximum=2048, step=8, value=rtv_params["width"], label="尺寸（宽度=高度）")
                    # 隐藏的宽高输入框，用于保持原有的参数结构
                    rtv_width = gr.Number(value=rtv_params["width"], visible=False)
                    rtv_height = gr.Number(value=rtv_params["height"], visible=False)
                    
                    # 当尺寸滑动条变化时，同步更新宽度和高度
                    rtv_size.change(fn=update_dimensions, inputs=[rtv_size], outputs=[rtv_width, rtv_height])
                
                with gr.Column(scale=1):
                    sampler_options = ["euler", "euler_cfg_pp", "euler_ancestral", "euler_ancestral_cfg_pp", 
                                     "heun", "heunpp2", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", 
                                     "dpmpp_2s_ancestral", "dpmpp_2s_ancestral_cfg_pp", "dpmpp_sde", "dpmpp_sde_gpu",
                                     "dpmpp_2m", "dpmpp_2m_cfg_pp", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", 
                                     "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", "ddpm", "LCM", "ipndm", "ipndm_v", 
                                     "deis", "res_multistep", "res_multistep_cfg_pp", "res_multistep_ancestral", 
                                     "res_multistep_ancestral_cfg", "gradient_estimation", "gradient_estimation_cfg_pp",
                                     "er_sde", "seeds_2", "uni_pc", "uni_pc_bh2", "ddim"]
                    rtv_sampler = gr.Dropdown(choices=sampler_options, value=rtv_params["sampler_name"], label="采样器")
                    
                    scheduler_options = ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta", "linear_quadratic", "kl_optimal"]
                    rtv_scheduler = gr.Dropdown(choices=scheduler_options, value=rtv_params["scheduler"], label="调度器")
            
            with gr.Row():
                rtv_steps = gr.Slider(minimum=1, maximum=100, step=1, value=rtv_params["steps"], label="采样步数")
                rtv_denoise = gr.Slider(minimum=0, maximum=1, step=0.01, value=rtv_params["denoise"], label="去噪强度")
                rtv_guidance = gr.Slider(minimum=1, maximum=20, step=0.1, value=rtv_params["guidance"], label="引导强度（数值越小越贴近提示词，数值越大AI自由发挥空间越大）")
            
            # 随机种子和随机生成按钮
            with gr.Row():
                rtv_noise_seed = gr.Number(value=rtv_params["noise_seed"], label="随机种子", precision=0)
                rtv_random_seed_btn = gr.Button("随机生成种子")
            
            # 生成按钮
            rtv_generate_btn = gr.Button("生成三视图", variant="primary", size="lg")
        
        # 右侧图片显示区
        with gr.Column(scale=1):
            gr.Markdown("### 生成结果预览")
            
            # 添加打开output文件夹的函数
            def open_output_folder_rtv():
                # 确保output文件夹存在
                os.makedirs("output", exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        os.system(f'explorer "{os.path.abspath("output")}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath("output")}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath("output")}"')
                    return "已打开output文件夹"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 添加状态显示区
            rtv_status_text = gr.Markdown("准备就绪")
            rtv_image_output = gr.Image(label="生成的图片", type="filepath")
            
            # 添加浏览输出文件夹按钮
            open_output_btn_rtv = gr.Button("浏览输出文件夹")
            output_folder_status_rtv = gr.Textbox(label="状态", visible=False)
            open_output_btn_rtv.click(fn=open_output_folder_rtv, inputs=[], outputs=output_folder_status_rtv)
    
    # 进度条
    rtv_progress_bar = gr.Progress()
    
    # 收集所有参数
    rtv_all_inputs = [
        rtv_size, rtv_sampler, rtv_scheduler, rtv_steps, rtv_denoise, rtv_guidance, rtv_noise_seed,
        rtv_lora_01, rtv_strength_01, rtv_lora_02, rtv_strength_02, rtv_lora_03, rtv_strength_03, rtv_lora_04, rtv_strength_04,
        rtv_prompt,  # 修改为单一提示词
        rtv_unet_model, rtv_clip_model1, rtv_clip_model2, rtv_vae_model, rtv_controlnet_model,  # 添加ControlNet模型
        rtv_image_name,  # 添加图片名称参数
        rtv_pose_image   # 添加姿势图参数
    ]
    
    # 修改generate_random_three_views函数的参数处理部分
    def generate_random_three_views(*args, progress=gr.Progress()):
        updated_params = {}
        
        # 将输入参数整合到一个字典中
        # 现在args[0]是rtv_size，同时设置width和height为相同的值
        size_value = args[0]
        # 确保尺寸在有效范围内
        size_value = int(max(512, min(size_value, 2048)))
        updated_params["width"] = size_value
        updated_params["height"] = size_value
        
        # 后续参数索引需要调整
        updated_params["sampler_name"] = args[1]
        updated_params["scheduler"] = args[2]
        updated_params["steps"] = args[3]
        updated_params["denoise"] = args[4]
        updated_params["guidance"] = args[5]
        updated_params["noise_seed"] = args[6]
        updated_params["lora_01"] = args[7]
        updated_params["strength_01"] = args[8]
        updated_params["lora_02"] = args[9]
        updated_params["strength_02"] = args[10]
        updated_params["lora_03"] = args[11]
        updated_params["strength_03"] = args[12]
        updated_params["lora_04"] = args[13]
        updated_params["strength_04"] = args[14]
        updated_params["prompt"] = args[15]  # 修改为单一提示词
        updated_params["unet_name"] = args[16]
        updated_params["clip_name1"] = args[17]
        updated_params["clip_name2"] = args[18]
        updated_params["vae_name"] = args[19]
        updated_params["controlnet_name"] = args[20]  # 添加ControlNet模型
        updated_params["image_name"] = args[21]  # 添加图片名称参数
        updated_params["pose_image"] = args[22]  # 添加姿势图参数
        
        # 处理姿势图路径
        pose_image_path = updated_params["pose_image"]
        if pose_image_path:
            # 如果是完整路径，则提取文件名
            pose_filename = os.path.basename(pose_image_path)
            print(f"使用姿势图: {pose_filename}")
            updated_params["pose_image"] = pose_filename
        
        # 打印尺寸信息
        print(f"使用图像尺寸: {updated_params['width']}x{updated_params['height']} (方形图)")
        print(f"使用ControlNet模型: {updated_params['controlnet_name']}")
        
        # 保存参数到JSON文件
        progress(0.05, "保存参数到配置文件...")
        saved_workflow = save_random_three_views_workflow(updated_params)
        
        # 创建状态更新的函数
        status_text = "三视图生成完成！"
        
        def progress_callback(value, message):
            nonlocal status_text
            status_text = message
            progress(value, message)
            print(f"UI进度更新: {value:.2f} - {message}")
        
        # 发送工作流到ComfyUI并获取生成结果
        result_image = send_workflow_to_comfyui(saved_workflow, progress_callback)
        
        # 返回生成的图像
        return result_image, status_text
    
    # 随机种子按钮的点击事件
    rtv_random_seed_btn.click(fn=generate_random_seed, inputs=None, outputs=rtv_noise_seed)
    
    # 生成按钮的点击事件
    rtv_generate_btn.click(
        fn=generate_random_three_views, 
        inputs=rtv_all_inputs, 
        outputs=[rtv_image_output, rtv_status_text],
        show_progress="full"
    )

# 读取放大及面部修复工作流文件
def load_magnified_facial_restoration_workflow():
    # 首先尝试当前目录的workflows文件夹
    try:
        with open("workflows/Magnified_facial_restoration.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        import sys
        import os
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Magnified_facial_restoration.json")
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误：无法找到Magnified_facial_restoration.json文件，已尝试路径: workflows/Magnified_facial_restoration.json 和 {workflow_path}")
            raise

# 保存放大及面部修复工作流文件
def save_magnified_facial_restoration_workflow_json(workflow_data):
    # 首先尝试当前目录的workflows文件夹
    try:
        os.makedirs("workflows", exist_ok=True)
        with open("workflows/Magnified_facial_restoration.json", "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        # 如果当前目录没有，则尝试相对于exe的目录
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(exe_dir, "workflows", "Magnified_facial_restoration.json")
        os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f, ensure_ascii=False, indent=2)

# 提取放大及面部修复可调节参数
def extract_magnified_facial_restoration_params():
    params = {
        # 设置默认参数
        "upscale_by": 2,
        "seed": 384340151733828,
        "steps": 22,
        "cfg": 1,
        "sampler_name": "deis",
        "scheduler": "beta",
        "denoise": 0.2,
        "tile_width": 1024,
        "tile_height": 1024,
        "mask_blur": 8,
        "tile_padding": 32,
        "seam_fix_mode": "None",
        "seam_fix_denoise": 1,
        "seam_fix_width": 64,
        "seam_fix_mask_blur": 8,
        "seam_fix_padding": 16,
        "force_uniform_tiles": True,
        "tiled_decode": False,
        "unet_name": "FLUX/flux-dev.safetensors",
        "clip_name1": "flux/t5xxl_fp16.safetensors",
        "clip_name2": "flux/clip_l.safetensors",
        "vae_name": "flux/ae.safetensors",
        "upscale_model": "4x-UltraSharp.pth",
        "positive_prompt": "Character sheet, white background, multiple views, from multiple angles, visible face, portrait, an ethereal silver-haired fox spirit wearing layered pink hanfu with white collar embroidery and intricate floral hairpins, delicate furry ears, serene expression, translucent chiffon skirts, ornate silver waist ornaments with tassels, soft cinematic lighting, simplified pale blue background, traditional Chinese fantasy art masterpiece, photography, sharp focus",
        "negative_prompt": "",
        "image_name": "character_sheet_flux",
        "input_image": None
    }
    
    # 如果工作流为空，直接返回默认参数
    if not magnified_facial_restoration_workflow:
        print("放大及面部修复工作流为空，使用默认参数")
        return params
    
    try:
        # 打印工作流的节点ID，帮助调试
        print(f"放大及面部修复工作流节点ID: {list(magnified_facial_restoration_workflow.keys())}")
        
        # 提取303节点参数（图片命名）
        if "303" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["303"]:
            if "string" in magnified_facial_restoration_workflow["303"]["inputs"]:
                params["image_name"] = magnified_facial_restoration_workflow["303"]["inputs"]["string"]
                print(f"从节点303提取图片名称: '{params['image_name']}'")
        
        # 提取361节点参数（输入图像）
        if "361" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["361"]:
            if "image" in magnified_facial_restoration_workflow["361"]["inputs"]:
                params["input_image"] = magnified_facial_restoration_workflow["361"]["inputs"]["image"]
                print(f"从节点361提取输入图像: {params['input_image']}")
        
        # 提取157节点参数（正向提示词）
        if "157" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["157"]:
            if "text" in magnified_facial_restoration_workflow["157"]["inputs"]:
                params["positive_prompt"] = magnified_facial_restoration_workflow["157"]["inputs"]["text"]
                print(f"从节点157提取正向提示词: {params['positive_prompt'][:30]}..." if len(params['positive_prompt']) > 30 else f"从节点157提取正向提示词: {params['positive_prompt']}")
        
        # 提取364节点参数（负向提示词）
        if "364" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["364"]:
            if "text" in magnified_facial_restoration_workflow["364"]["inputs"]:
                params["negative_prompt"] = magnified_facial_restoration_workflow["364"]["inputs"]["text"]
                print(f"从节点364提取负向提示词: {params['negative_prompt'][:30]}..." if len(params['negative_prompt']) > 30 else f"从节点364提取负向提示词: {params['negative_prompt']}")
        
        # 提取82节点参数（SD放大参数）
        if "82" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["82"]:
            sd_upscale_params = magnified_facial_restoration_workflow["82"]["inputs"]
            for key in ["upscale_by", "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", 
                       "tile_width", "tile_height", "mask_blur", "tile_padding", "seam_fix_mode", 
                       "seam_fix_denoise", "seam_fix_width", "seam_fix_mask_blur", "seam_fix_padding", 
                       "force_uniform_tiles", "tiled_decode"]:
                if key in sd_upscale_params:
                    params[key] = sd_upscale_params[key]
            print(f"从节点82提取SD放大参数")
        
        # 提取83节点参数（放大模型）
        if "83" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["83"]:
            if "model_name" in magnified_facial_restoration_workflow["83"]["inputs"]:
                params["upscale_model"] = magnified_facial_restoration_workflow["83"]["inputs"]["model_name"]
                print(f"从节点83提取放大模型: {params['upscale_model']}")
        
        # 提取161节点参数（UNET模型）
        if "161" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["161"]:
            if "unet_name" in magnified_facial_restoration_workflow["161"]["inputs"]:
                params["unet_name"] = magnified_facial_restoration_workflow["161"]["inputs"]["unet_name"]
                print(f"从节点161提取UNET模型: {params['unet_name']}")
        
        # 提取160节点参数（CLIP模型）
        if "160" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["160"]:
            if "clip_name1" in magnified_facial_restoration_workflow["160"]["inputs"]:
                params["clip_name1"] = magnified_facial_restoration_workflow["160"]["inputs"]["clip_name1"]
            if "clip_name2" in magnified_facial_restoration_workflow["160"]["inputs"]:
                params["clip_name2"] = magnified_facial_restoration_workflow["160"]["inputs"]["clip_name2"]
            print(f"从节点160提取CLIP模型")
        
        # 提取159节点参数（VAE模型）
        if "159" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["159"]:
            if "vae_name" in magnified_facial_restoration_workflow["159"]["inputs"]:
                params["vae_name"] = magnified_facial_restoration_workflow["159"]["inputs"]["vae_name"]
                print(f"从节点159提取VAE模型: {params['vae_name']}")
        
        # 注释掉183节点参数提取，因为该节点未使用
        # # 提取183节点参数（面部细化参数）
        # if "183" in magnified_facial_restoration_workflow and "inputs" in magnified_facial_restoration_workflow["183"]:
        #     if "guide_size" in magnified_facial_restoration_workflow["183"]["inputs"]:
        #         params["guide_size"] = magnified_facial_restoration_workflow["183"]["inputs"]["guide_size"]
        #         print(f"从节点183提取guide_size: {params['guide_size']}")
        #     # 可以提取更多的面部细化参数...
            
    except Exception as e:
        print(f"提取放大及面部修复参数时出错: {e}")
        import traceback
        traceback.print_exc()
    
    return params

# 保存放大及面部修复调整后的参数
def save_magnified_facial_restoration_workflow(params):
    workflow_copy = copy.deepcopy(magnified_facial_restoration_workflow)
    
    # 如果工作流为空，使用默认结构
    if not workflow_copy:
        logging.warning("放大及面部修复工作流为空，无法保存参数")
        return workflow_copy
    
    try:
        # 更新303节点参数（图片命名）
        if "303" in workflow_copy:
            if "inputs" not in workflow_copy["303"]:
                workflow_copy["303"]["inputs"] = {}
            workflow_copy["303"]["inputs"]["string"] = params["image_name"]
            print(f"已将图片名称 '{params['image_name']}' 保存到放大及面部修复工作流303节点")
        
        # 更新361节点参数（输入图像）
        if params.get("input_image") and "361" in workflow_copy:
            if "inputs" not in workflow_copy["361"]:
                workflow_copy["361"]["inputs"] = {}
            # ComfyUI期望的格式是直接使用图片名称，它会自动在input目录下查找
            # 确保只使用文件名，而不是完整路径
            if params["input_image"] and isinstance(params["input_image"], str):
                # 如果是路径，只获取文件名部分
                filename = os.path.basename(params["input_image"])
                workflow_copy["361"]["inputs"]["image"] = filename
                print(f"已将输入图像 {filename} 保存到放大及面部修复工作流361节点")
            else:
                workflow_copy["361"]["inputs"]["image"] = params["input_image"]
                print(f"已将输入图像 {params['input_image']} 保存到放大及面部修复工作流361节点")
        
        # 更新157节点参数（正向提示词）
        if "157" in workflow_copy:
            if "inputs" not in workflow_copy["157"]:
                workflow_copy["157"]["inputs"] = {}
            workflow_copy["157"]["inputs"]["text"] = params["positive_prompt"]
            print(f"已将正向提示词保存到放大及面部修复工作流157节点")
        
        # 更新364节点参数（负向提示词）
        if "364" in workflow_copy:
            if "inputs" not in workflow_copy["364"]:
                workflow_copy["364"]["inputs"] = {}
            workflow_copy["364"]["inputs"]["text"] = params["negative_prompt"]
            print(f"已将负向提示词保存到放大及面部修复工作流364节点")
        
        # 更新82节点参数（SD放大参数）
        if "82" in workflow_copy:
            if "inputs" not in workflow_copy["82"]:
                workflow_copy["82"]["inputs"] = {}
            
            # 更新所有SD放大参数
            for key in ["upscale_by", "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", 
                       "tile_width", "tile_height", "mask_blur", "tile_padding", "seam_fix_mode", 
                       "seam_fix_denoise", "seam_fix_width", "seam_fix_mask_blur", "seam_fix_padding", 
                       "force_uniform_tiles", "tiled_decode"]:
                if key in params:
                    workflow_copy["82"]["inputs"][key] = params[key]
            print(f"已将SD放大参数保存到放大及面部修复工作流82节点")
        
        # 更新83节点参数（放大模型）
        if "83" in workflow_copy:
            if "inputs" not in workflow_copy["83"]:
                workflow_copy["83"]["inputs"] = {}
            workflow_copy["83"]["inputs"]["model_name"] = params["upscale_model"]
            print(f"已将放大模型 {params['upscale_model']} 保存到放大及面部修复工作流83节点")
        
        # 更新161节点参数（UNET模型）
        if "161" in workflow_copy:
            if "inputs" not in workflow_copy["161"]:
                workflow_copy["161"]["inputs"] = {}
            workflow_copy["161"]["inputs"]["unet_name"] = params["unet_name"]
            print(f"已将UNET模型 {params['unet_name']} 保存到放大及面部修复工作流161节点")
        
        # 更新160节点参数（CLIP模型）
        if "160" in workflow_copy:
            if "inputs" not in workflow_copy["160"]:
                workflow_copy["160"]["inputs"] = {}
            workflow_copy["160"]["inputs"]["clip_name1"] = params["clip_name1"]
            workflow_copy["160"]["inputs"]["clip_name2"] = params["clip_name2"]
            print(f"已将CLIP模型保存到放大及面部修复工作流160节点")
        
        # 更新159节点参数（VAE模型）
        if "159" in workflow_copy:
            if "inputs" not in workflow_copy["159"]:
                workflow_copy["159"]["inputs"] = {}
            workflow_copy["159"]["inputs"]["vae_name"] = params["vae_name"]
            print(f"已将VAE模型 {params['vae_name']} 保存到放大及面部修复工作流159节点")
        
        # 可以添加更多参数的保存...
        
    except Exception as e:
        print(f"保存放大及面部修复参数时出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 保存工作流
    save_magnified_facial_restoration_workflow_json(workflow_copy)
    return workflow_copy

# 提取放大及面部修复参数
magnified_facial_restoration_params = extract_magnified_facial_restoration_params()

# 放大及面部修复界面
with gr.Blocks(title="图片放大 - ComfyUI接口") as magnified_facial_restoration_demo:
    gr.Markdown("# 图片放大")
    
    # 确保先提取参数
    mfr_params = extract_magnified_facial_restoration_params()
    print(f"界面初始化时的图片名称: '{mfr_params.get('image_name', '')}'")
    
    # 生成放大图像函数
    def generate_magnified_facial_restoration(*args, progress=gr.Progress()):
        input_image_path = args[0]  # 输入图像路径
        image_name = args[1]  # 图片名称
        positive_prompt = args[2]  # 正向提示词
        negative_prompt = args[3]  # 负向提示词
        unet_name = args[4]  # UNET模型
        clip_name1 = args[5]  # CLIP模型1
        clip_name2 = args[6]  # CLIP模型2
        vae_name = args[7]  # VAE模型
        upscale_model = args[8]  # 放大模型
        upscale_by = args[9]  # 放大倍数
        sampler_name = args[10]  # 采样器
        scheduler = args[11]  # 调度器
        steps = args[12]  # 采样步数
        cfg = args[13]  # CFG
        denoise = args[14]  # 去噪强度
        tile_width = args[15]  # 切片宽度
        tile_height = args[16]  # 切片高度
        tile_padding = args[17]  # 切片边距
        mask_blur = args[18]  # 遮罩模糊
        seam_fix_mode = args[19]  # 缝合修复模式
        seam_fix_denoise = args[20]  # 缝合修复去噪
        seam_fix_width = args[21]  # 缝合修复宽度
        seam_fix_mask_blur = args[22]  # 缝合遮罩模糊
        seam_fix_padding = args[23]  # 缝合修复边距
        force_uniform_tiles = args[24]  # 强制统一切片
        tiled_decode = args[25]  # 切片解码
        seed = args[26]  # 随机种子
        image_path_text = args[27]  # 图像路径文本
        
        # 优先使用文本框中的图片路径（如果有）
        if image_path_text and (image_path_text.startswith("已保存图片:") or image_path_text.startswith("已选择输入图像:")):
            saved_path = image_path_text.replace("已保存图片:", "").replace("已选择输入图像:", "").strip()
            if "(" in saved_path:
                saved_path = saved_path.split("(")[0].strip()
            if os.path.exists(saved_path):
                input_image_path = saved_path
                print(f"使用文本框中的图片路径: {input_image_path}")
        
        if not input_image_path:
            return None, "错误：请先上传或选择输入图像"
        
        # 确保input_image_path是一个有效的文件路径
        if not os.path.exists(input_image_path):
            return None, f"错误：输入图像路径无效 - {input_image_path}"
        
        # 打印使用的输入图像
        print(f"使用输入图像: {input_image_path}")
        
        # 检查图片是否已经在ComfyUI input文件夹中
        comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
        os.makedirs(comfyui_input_path, exist_ok=True)
        filename = os.path.basename(input_image_path)
        comfyui_file_path = os.path.join(comfyui_input_path, filename)
        
        # 如果不在ComfyUI input文件夹中，复制过去
        if not input_image_path.startswith(WSL_COMFYUI_PATH):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = os.path.splitext(filename)[1].lower() or ".png"
            new_filename = f"image_{timestamp}{ext}"
            comfyui_file_path = os.path.join(comfyui_input_path, new_filename)
            
            try:
                shutil.copy2(input_image_path, comfyui_file_path)
                print(f"已将图片从 {input_image_path} 复制到 {comfyui_file_path}")
                filename = new_filename
            except Exception as e:
                print(f"复制图片出错: {e}")
                return None, f"错误：复制图片到ComfyUI失败 - {str(e)}"
        
        # 将输入参数整合到一个字典中
        updated_params = {
            "image_name": image_name,
            "input_image": filename,  # 仅使用文件名
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "unet_name": unet_name,
            "clip_name1": clip_name1,
            "clip_name2": clip_name2,
            "vae_name": vae_name,
            "upscale_model": upscale_model,
            "upscale_by": upscale_by,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "steps": steps,
            "cfg": cfg,
            "denoise": denoise,
            "tile_width": tile_width,
            "tile_height": tile_height,
            "tile_padding": tile_padding,
            "mask_blur": mask_blur,
            "seam_fix_mode": seam_fix_mode,
            "seam_fix_denoise": seam_fix_denoise,
            "seam_fix_width": seam_fix_width,
            "seam_fix_mask_blur": seam_fix_mask_blur,
            "seam_fix_padding": seam_fix_padding,
            "force_uniform_tiles": force_uniform_tiles,
            "tiled_decode": tiled_decode,
            "seed": seed
        }
        
        # 保存参数到JSON文件
        progress(0.05, "保存参数到配置文件...")
        saved_workflow = save_magnified_facial_restoration_workflow(updated_params)
        
        # 创建状态更新的函数
        status_text = "图像生成完成！"
        
        def progress_callback(value, message):
            nonlocal status_text
            status_text = message
            progress(value, message)
            print(f"UI进度更新: {value:.2f} - {message}")
        
        # 发送工作流到ComfyUI并获取生成结果
        try:
            # 将输入图像路径作为额外参数传入
            result_image = send_workflow_to_comfyui(saved_workflow, progress_callback, input_image_path=input_image_path)
            
            # 如果生成成功，显示成功信息
            if result_image and os.path.exists(result_image):
                return result_image, "图像生成完成！"
            else:
                return None, "图像生成失败，未能获取结果图像"
        except Exception as e:
            import traceback
            error_msg = f"处理过程中出错: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return None, error_msg
    
    with gr.Row():
        # 左侧参数控制区
        with gr.Column(scale=2):
            # 添加"给图片取过名字呗"功能（放在最顶部）
            gr.Markdown("### 给图片取过名字呗")
            mfr_image_name = gr.Textbox(
                value=mfr_params.get("image_name", ""), 
                label="输入图片名称", 
                lines=1,
                placeholder="请输入图片名称..."
            )
            
            # 添加"上传输入图像"功能
            gr.Markdown("### 上传输入图像")
            
            # 参考图生图界面的图片上传功能
            def save_mfr_image_to_input_folder(img):
                if img is None:
                    return None, "未上传图片", "图片尺寸: 未知", None
                    
                # 确保ComfyUI的input文件夹存在
                comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
                os.makedirs(comfyui_input_path, exist_ok=True)
                
                # 获取当前时间作为文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 构建文件路径
                if isinstance(img, str):  # 如果已经是文件路径
                    ext = os.path.splitext(img)[1].lower()
                    if not ext:
                        ext = ".png"  # 默认扩展名
                    file_path = os.path.join(comfyui_input_path, f"image_{timestamp}{ext}")
                    
                    # 复制文件
                    shutil.copy2(img, file_path)
                    
                    # 获取图片尺寸
                    try:
                        with Image.open(file_path) as img_obj:
                            width, height = img_obj.size
                            dimension_text = f"图片尺寸: {width} x {height} 像素"
                    except Exception as e:
                        dimension_text = f"无法获取图片尺寸: {str(e)}"
                else:  # 如果是PIL图像对象
                    file_path = os.path.join(comfyui_input_path, f"image_{timestamp}.png")
                    img.save(file_path)
                    
                    # 获取图片尺寸
                    try:
                        width, height = img.size
                        dimension_text = f"图片尺寸: {width} x {height} 像素"
                    except Exception as e:
                        dimension_text = f"无法获取图片尺寸: {str(e)}"
                
                # 获取文件名（不包含路径）
                filename = os.path.basename(file_path)
                
                print(f"已保存输入图像到ComfyUI的input文件夹: {file_path}")
                
                # 更新下拉菜单选项
                new_images = get_input_folder_images()
                dropdown_choices = []
                for name in new_images:
                    full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                    try:
                        size_kb = os.path.getsize(full_path) // 1024
                        dropdown_choices.append((f"{name} ({size_kb} KB)", full_path))
                    except Exception as e:
                        print(f"获取文件大小出错: {e}")
                
                return file_path, f"已保存图片: {file_path} (文件名: {filename})", dimension_text, gr.update(choices=dropdown_choices, value=file_path)
            
            # 打开input文件夹的函数
            def open_mfr_input_folder():
                # 确保ComfyUI的input文件夹存在
                comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
                os.makedirs(comfyui_input_path, exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        # 直接使用WSL路径打开，不转换为本地路径
                        os.system(f'explorer "{comfyui_input_path}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath(comfyui_input_path)}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath(comfyui_input_path)}"')
                    return f"已打开ComfyUI的input文件夹: {comfyui_input_path}"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 选择现有图片的函数
            def select_existing_mfr_image(file_path):
                if not file_path or not os.path.exists(file_path):
                    return None, "未选择图片", "图片尺寸: 未知"
                
                # 获取图片尺寸
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        dimension_text = f"图片尺寸: {width} x {height} 像素"
                except Exception as e:
                    dimension_text = f"无法获取图片尺寸: {str(e)}"
                
                return file_path, f"已选择输入图像: {file_path}", dimension_text
            
            # 图片上传组件
            mfr_input_image = gr.Image(label="上传输入图像", type="filepath")
            mfr_image_path_text = gr.Textbox(label="输入图像路径", interactive=False)
            mfr_image_dimensions = gr.Textbox(label="输入图像尺寸", interactive=False)
            
            # 获取文件夹中所有图片
            existing_images = get_input_folder_images()
            image_choices = []
            for name in existing_images:
                full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                try:
                    size_kb = os.path.getsize(full_path) // 1024
                    image_choices.append((f"{name} ({size_kb} KB)", full_path))
                except Exception as e:
                    print(f"获取文件大小出错: {e}")
                    
            # 下面是原始有错误的代码
            # image_choices = [(f"{name} ({os.path.getsize(path) // 1024} KB)", path) for name, path in existing_images]
            
            # 添加图片选择下拉菜单
            mfr_image_dropdown = gr.Dropdown(
                choices=image_choices,
                label="选择已有图片",
                info="选择已存在的图片而不是重新上传",
                type="value"
            )
            
            # 刷新图片列表按钮
            mfr_refresh_btn = gr.Button("刷新图片列表")
            
            def refresh_mfr_image_list():
                new_images = get_input_folder_images()
                new_choices = []
                for name in new_images:
                    full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                    try:
                        size_kb = os.path.getsize(full_path) // 1024
                        new_choices.append((f"{name} ({size_kb} KB)", full_path))
                    except Exception as e:
                        print(f"刷新图片列表时获取文件大小出错: {e}")
                return gr.update(choices=new_choices)
            
            mfr_refresh_btn.click(fn=refresh_mfr_image_list, inputs=[], outputs=[mfr_image_dropdown])
            
            # 图片上传处理
            mfr_input_image.upload(
                fn=save_mfr_image_to_input_folder, 
                inputs=mfr_input_image, 
                outputs=[mfr_input_image, mfr_image_path_text, mfr_image_dimensions, mfr_image_dropdown]
            )
            
            # 下拉菜单选择图片事件
            mfr_image_dropdown.change(
                fn=select_existing_mfr_image, 
                inputs=[mfr_image_dropdown], 
                outputs=[mfr_input_image, mfr_image_path_text, mfr_image_dimensions]
            )
            
            # 添加浏览文件夹按钮
            mfr_open_folder_btn = gr.Button("浏览图片文件夹")
            mfr_folder_status = gr.Textbox(label="状态", visible=False)
            mfr_open_folder_btn.click(fn=open_mfr_input_folder, inputs=[], outputs=mfr_folder_status)
            
            # 提示词部分
            gr.Markdown("### 提示词")
            mfr_positive_prompt = gr.Textbox(value=mfr_params.get("positive_prompt", ""), label="正向提示词", lines=3)
            # 负向提示词设置为不可见，但保留其功能
            mfr_negative_prompt = gr.Textbox(value="", label="负向提示词", lines=2, visible=False)
            
            # 模型选择部分
            gr.Markdown("### 模型选择 (已配置好，一般不需更改)")
            
            # UNET模型选择
            unet_models = ensure_model_in_list(models.get("unet", []), mfr_params.get("unet_name", ""))
            mfr_unet_model = gr.Dropdown(choices=unet_models, value=mfr_params.get("unet_name", ""), label="UNET模型", allow_custom_value=True)
            
            # CLIP模型选择
            clip_models = models.get("clip", [])
            clip_models = ensure_model_in_list(clip_models, mfr_params.get("clip_name1", ""))
            clip_models = ensure_model_in_list(clip_models, mfr_params.get("clip_name2", ""))
            with gr.Row():
                mfr_clip_model1 = gr.Dropdown(choices=clip_models, value=mfr_params.get("clip_name1", ""), label="CLIP模型1", allow_custom_value=True)
                mfr_clip_model2 = gr.Dropdown(choices=clip_models, value=mfr_params.get("clip_name2", ""), label="CLIP模型2", allow_custom_value=True)
            
            # VAE模型选择
            vae_models = ensure_model_in_list(models.get("vae", []), mfr_params.get("vae_name", ""))
            mfr_vae_model = gr.Dropdown(choices=vae_models, value=mfr_params.get("vae_name", ""), label="VAE模型", allow_custom_value=True)
            
            # 放大模型选择
            # 获取放大模型列表 - 临时简单实现
            upscale_models = ["4x-UltraSharp.pth", "4x-AnimeSharp.pth", "4x-UltraSharp.pth", "ESRGAN_4x.pth", "RealESRGAN_x4plus.pth", "RealESRGAN_x4plus_anime_6B.pth"]
            upscale_models = ensure_model_in_list(upscale_models, mfr_params.get("upscale_model", ""))
            mfr_upscale_model = gr.Dropdown(choices=upscale_models, value=mfr_params.get("upscale_model", ""), label="放大模型", allow_custom_value=True)
            
            # SD放大参数
            gr.Markdown("### SD放大参数")
            
            # 放大倍数
            mfr_upscale_by = gr.Slider(minimum=1, maximum=4, step=0.1, value=mfr_params.get("upscale_by", 2), label="放大倍数")
            
            # SD采样参数
            with gr.Row():
                sampler_options = ["euler", "euler_cfg_pp", "euler_ancestral", "euler_ancestral_cfg_pp", 
                                 "heun", "heunpp2", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", 
                                 "dpmpp_2s_ancestral", "dpmpp_2s_ancestral_cfg_pp", "dpmpp_sde", "dpmpp_sde_gpu",
                                 "dpmpp_2m", "dpmpp_2m_cfg_pp", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", 
                                 "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", "ddpm", "LCM", "ipndm", "ipndm_v", 
                                 "deis", "res_multistep", "res_multistep_cfg_pp", "res_multistep_ancestral", 
                                 "res_multistep_ancestral_cfg", "gradient_estimation", "gradient_estimation_cfg_pp",
                                 "er_sde", "seeds_2", "uni_pc", "uni_pc_bh2", "ddim"]
                mfr_sampler = gr.Dropdown(choices=sampler_options, value=mfr_params.get("sampler_name", "deis"), label="采样器")
                
                scheduler_options = ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "beta", "linear_quadratic", "kl_optimal"]
                mfr_scheduler = gr.Dropdown(choices=scheduler_options, value=mfr_params.get("scheduler", "beta"), label="调度器")
            
            with gr.Row():
                mfr_steps = gr.Slider(minimum=1, maximum=50, step=1, value=mfr_params.get("steps", 22), label="采样步数")
                mfr_cfg = gr.Slider(minimum=1, maximum=10, step=0.1, value=mfr_params.get("cfg", 1), label="CFG")
                mfr_denoise = gr.Slider(minimum=0, maximum=1, step=0.01, value=mfr_params.get("denoise", 0.2), label="去噪强度")
            
            # 切片参数
            gr.Markdown("### 切片参数")
            with gr.Row():
                mfr_tile_width = gr.Slider(minimum=256, maximum=2048, step=8, value=mfr_params.get("tile_width", 1024), label="切片宽度")
                mfr_tile_height = gr.Slider(minimum=256, maximum=2048, step=8, value=mfr_params.get("tile_height", 1024), label="切片高度")
            
            with gr.Row():
                mfr_tile_padding = gr.Slider(minimum=0, maximum=256, step=4, value=mfr_params.get("tile_padding", 32), label="切片边距")
                mfr_mask_blur = gr.Slider(minimum=0, maximum=64, step=1, value=mfr_params.get("mask_blur", 8), label="遮罩模糊")
            
            # 缝合修复选项
            gr.Markdown("### 缝合修复选项")
            seam_fix_modes = ["None", "Band Pass", "Half Tile", "Half Tile + Intersections"]
            mfr_seam_fix_mode = gr.Dropdown(choices=seam_fix_modes, value=mfr_params.get("seam_fix_mode", "None"), label="缝合修复模式")
            
            with gr.Row():
                mfr_seam_fix_denoise = gr.Slider(minimum=0, maximum=1, step=0.01, value=mfr_params.get("seam_fix_denoise", 1), label="缝合修复去噪")
                mfr_seam_fix_width = gr.Slider(minimum=0, maximum=256, step=1, value=mfr_params.get("seam_fix_width", 64), label="缝合修复宽度")
            
            with gr.Row():
                mfr_seam_fix_mask_blur = gr.Slider(minimum=0, maximum=64, step=1, value=mfr_params.get("seam_fix_mask_blur", 8), label="缝合遮罩模糊")
                mfr_seam_fix_padding = gr.Slider(minimum=0, maximum=256, step=1, value=mfr_params.get("seam_fix_padding", 16), label="缝合修复边距")
            
            # 其他选项
            gr.Markdown("### 其他选项")
            with gr.Row():
                mfr_force_uniform_tiles = gr.Checkbox(value=mfr_params.get("force_uniform_tiles", True), label="强制统一切片")
                mfr_tiled_decode = gr.Checkbox(value=mfr_params.get("tiled_decode", False), label="切片解码")
            
            # 随机种子和随机生成按钮
            with gr.Row():
                mfr_seed = gr.Number(value=mfr_params.get("seed", 384340151733828), label="随机种子", precision=0)
                mfr_random_seed_btn = gr.Button("随机生成种子")
            
            # 生成按钮
            mfr_generate_btn = gr.Button("生成放大图像", variant="primary", size="lg")
        
        # 右侧图片显示区
        with gr.Column(scale=1):
            gr.Markdown("### 生成结果预览")
            
            # 添加打开output文件夹的函数
            def open_output_folder_mfr():
                # 确保output文件夹存在
                os.makedirs("output", exist_ok=True)
                
                # 获取当前操作系统
                system = platform.system()
                
                # 根据操作系统使用不同的命令打开文件夹
                try:
                    if system == "Windows":
                        os.system(f'explorer "{os.path.abspath("output")}"')
                    elif system == "Darwin":  # macOS
                        os.system(f'open "{os.path.abspath("output")}"')
                    elif system == "Linux":
                        os.system(f'xdg-open "{os.path.abspath("output")}"')
                    return "已打开output文件夹"
                except Exception as e:
                    return f"打开文件夹出错: {str(e)}"
            
            # 添加状态显示区
            mfr_status_text = gr.Markdown("准备就绪")
            mfr_image_output = gr.Image(label="生成的图片", type="filepath")
            
            # 添加浏览输出文件夹按钮
            open_output_btn_mfr = gr.Button("浏览输出文件夹")
            output_folder_status_mfr = gr.Textbox(label="状态", visible=False)
            open_output_btn_mfr.click(fn=open_output_folder_mfr, inputs=[], outputs=output_folder_status_mfr)
    
    # 进度条
    mfr_progress_bar = gr.Progress()
    
    # 收集所有参数
    mfr_all_inputs = [
        mfr_image_name,  # 添加图片名称参数
        mfr_input_image,  # 添加输入图像
        mfr_sampler, mfr_scheduler, mfr_steps, mfr_cfg, mfr_denoise,
        mfr_tile_width, mfr_tile_height, mfr_tile_padding, mfr_mask_blur,
        mfr_seam_fix_mode, mfr_seam_fix_denoise, mfr_seam_fix_width, mfr_seam_fix_mask_blur, mfr_seam_fix_padding,
        mfr_force_uniform_tiles, mfr_tiled_decode, mfr_seed,
        mfr_upscale_by, mfr_unet_model, mfr_clip_model1, mfr_clip_model2, mfr_vae_model, mfr_upscale_model,
        mfr_positive_prompt, mfr_negative_prompt  # 添加更多参数
    ]
    
    # 生成图像按钮的点击事件
    def generate_mfr(*args, progress=gr.Progress()):
        updated_params = {}
        
        # 将输入参数整合到一个字典中
        updated_params["image_name"] = args[0]
        updated_params["input_image"] = args[1]
        updated_params["sampler_name"] = args[2]
        updated_params["scheduler"] = args[3]
        updated_params["steps"] = args[4]
        updated_params["cfg"] = args[5]
        updated_params["denoise"] = args[6]
        updated_params["tile_width"] = args[7]
        updated_params["tile_height"] = args[8]
        updated_params["mask_blur"] = args[9]
        updated_params["tile_padding"] = args[10]
        updated_params["seam_fix_mode"] = args[11]
        updated_params["seam_fix_denoise"] = args[12]
        updated_params["seam_fix_width"] = args[13]
        updated_params["seam_fix_mask_blur"] = args[14]
        updated_params["seam_fix_padding"] = args[15]
        updated_params["force_uniform_tiles"] = args[16]
        updated_params["tiled_decode"] = args[17]
        updated_params["seed"] = args[18]
        updated_params["upscale_by"] = args[19]
        updated_params["unet_name"] = args[20]
        updated_params["clip_name1"] = args[21]
        updated_params["clip_name2"] = args[22]
        updated_params["vae_name"] = args[23]
        updated_params["upscale_model"] = args[24]
        updated_params["positive_prompt"] = args[25]
        updated_params["negative_prompt"] = args[26]
        
        # 保存参数到JSON文件
        progress(0.05, "保存参数到配置文件...")
        saved_workflow = save_magnified_facial_restoration_workflow(updated_params)
        
        # 创建状态更新的函数
        status_text = "图像生成完成！"
        is_completed = False
        
        def progress_callback(value, message):
            nonlocal status_text, is_completed
            status_text = message
            progress(value, message)
            print(f"UI进度更新: {value:.2f} - {message}")
            
            # 当进度达到0.95时，增加提示信息
            if value >= 0.95 and not is_completed:
                status_text = "完成工作流执行，正在寻找并合成最终图像，请耐心等待..."
                progress(0.95, status_text)
                print("放大工作流执行接近完成，正在等待最终图像合成...")
        
        # 发送工作流到ComfyUI并获取生成结果
        try:
            result_image = send_workflow_to_comfyui(saved_workflow, progress_callback)
            is_completed = True
            
            # 检查是否成功获取图像
            if result_image:
                status_text = "图像生成完成！"
                progress(1.0, "完成")
            else:
                # 如果没有获取到图像，尝试查找最新的图像
                print("未找到生成的图像，尝试查找最新保存的图像...")
                status_text = "未找到生成的图像，尝试查找最新保存的图像..."
                progress(0.95, status_text)
                
                result_image = find_latest_image()
                if result_image:
                    status_text = "已找到最新保存的图像"
                    progress(1.0, "完成")
                else:
                    status_text = "未能找到任何生成的图像"
                    progress(1.0, "完成")
        except Exception as e:
            print(f"生成图像过程中出错: {e}")
            import traceback
            traceback.print_exc()
            status_text = f"生成图像失败: {str(e)}"
            is_completed = True
            # 尝试查找最新的图像作为备选
            result_image = find_latest_image()
        
        # 返回生成的图像
        return result_image, status_text
    
    # 随机种子按钮的点击事件
    mfr_random_seed_btn.click(fn=generate_random_seed, inputs=None, outputs=mfr_seed)
    
    # 生成按钮的点击事件
    mfr_generate_btn.click(
        fn=generate_mfr, 
        inputs=mfr_all_inputs, 
        outputs=[mfr_image_output, mfr_status_text],
        show_progress="full"
    )

# 保存面部修复调整后的参数
# 提取面部修复可调节参数
def extract_facial_restoration_params():
    params = {
        # 设置默认参数
        "seed": 12346,
        "steps": 20,
        "cfg": 1,
        "sampler_name": "deis",
        "scheduler": "beta",
        "denoise": 0.22,
        "guide_size": 512,
        "guide_size_for": True,
        "max_size": 1024,
        "feather": 5,
        "noise_mask": True,
        "force_inpaint": True,
        "bbox_threshold": 0.5,
        "bbox_dilation": 20,
        "bbox_crop_factor": 3,
        "sam_detection_hint": "center-1",
        "sam_dilation": 0,
        "sam_threshold": 0.93,
        "sam_bbox_expansion": 0,
        "sam_mask_hint_threshold": 0.7,
        "sam_mask_hint_use_negative": "False",
        "drop_size": 10,
        "refiner_ratio": 0.2,
        "cycle": 1,
        "inpaint_model": False,
        "noise_mask_feather": 20,
        "tiled_encode": False,
        "tiled_decode": False,
        "unet_name": "FLUX/flux-dev.safetensors",
        "clip_name1": "flux/t5xxl_fp16.safetensors",
        "clip_name2": "flux/clip_l.safetensors",
        "vae_name": "flux/ae.safetensors",
        "positive_prompt": "Character sheet, white background, multiple views, from multiple angles, visible face, portrait, an ethereal silver-haired fox spirit wearing layered pink hanfu with white collar embroidery and intricate floral hairpins, delicate furry ears, serene expression, translucent chiffon skirts, ornate silver waist ornaments with tassels, soft cinematic lighting, simplified pale blue background, traditional Chinese fantasy art masterpiece, photography, sharp focus",
        "negative_prompt": "",
        "image_name": "character_sheet_flux",
        "input_image": None,
        "bbox_model": "bbox/face_yolov8m.pt"
    }
    
    # 如果工作流为空，直接返回默认参数
    if not facial_restoration_workflow:
        print("面部修复工作流为空，使用默认参数")
        return params
    
    try:
        # 打印工作流的节点ID，帮助调试
        print(f"面部修复工作流节点ID: {list(facial_restoration_workflow.keys())}")
        
        # 提取303节点参数（图片命名）
        if "303" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["303"]:
            if "string" in facial_restoration_workflow["303"]["inputs"]:
                params["image_name"] = facial_restoration_workflow["303"]["inputs"]["string"]
                print(f"从节点303提取图片名称: '{params['image_name']}'")
        
        # 提取361节点参数（输入图像）
        if "361" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["361"]:
            if "image" in facial_restoration_workflow["361"]["inputs"]:
                params["input_image"] = facial_restoration_workflow["361"]["inputs"]["image"]
                print(f"从节点361提取输入图像: {params['input_image']}")
        
        # 提取157节点参数（正向提示词）
        if "157" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["157"]:
            if "text" in facial_restoration_workflow["157"]["inputs"]:
                params["positive_prompt"] = facial_restoration_workflow["157"]["inputs"]["text"]
                print(f"从节点157提取正向提示词: {params['positive_prompt'][:30]}..." if len(params['positive_prompt']) > 30 else f"从节点157提取正向提示词: {params['positive_prompt']}")
        
        # 提取364节点参数（负向提示词）
        if "364" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["364"]:
            if "text" in facial_restoration_workflow["364"]["inputs"]:
                params["negative_prompt"] = facial_restoration_workflow["364"]["inputs"]["text"]
                print(f"从节点364提取负向提示词: {params['negative_prompt'][:30]}..." if len(params['negative_prompt']) > 30 else f"从节点364提取负向提示词: {params['negative_prompt']}")
        
        # 提取18节点参数（检测加载器）
        if "18" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["18"]:
            if "model_name" in facial_restoration_workflow["18"]["inputs"]:
                params["bbox_model"] = facial_restoration_workflow["18"]["inputs"]["model_name"]
                print(f"从节点18提取检测模型: {params['bbox_model']}")
        
        # 提取183节点参数（面部细化参数）
        if "183" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["183"]:
            face_detailer_params = facial_restoration_workflow["183"]["inputs"]
            for key in ["guide_size", "guide_size_for", "max_size", "seed", "steps", "cfg", 
                       "sampler_name", "scheduler", "denoise", "feather", "noise_mask", 
                       "force_inpaint", "bbox_threshold", "bbox_dilation", "bbox_crop_factor",
                       "sam_detection_hint", "sam_dilation", "sam_threshold", "sam_bbox_expansion", 
                       "sam_mask_hint_threshold", "sam_mask_hint_use_negative", "drop_size", 
                       "refiner_ratio", "cycle", "inpaint_model", "noise_mask_feather", 
                       "tiled_encode", "tiled_decode"]:
                if key in face_detailer_params:
                    params[key] = face_detailer_params[key]
            print(f"从节点183提取面部细化参数")
        
        # 提取161节点参数（UNET模型）
        if "161" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["161"]:
            if "unet_name" in facial_restoration_workflow["161"]["inputs"]:
                params["unet_name"] = facial_restoration_workflow["161"]["inputs"]["unet_name"]
                print(f"从节点161提取UNET模型: {params['unet_name']}")
        
        # 提取160节点参数（CLIP模型）
        if "160" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["160"]:
            if "clip_name1" in facial_restoration_workflow["160"]["inputs"]:
                params["clip_name1"] = facial_restoration_workflow["160"]["inputs"]["clip_name1"]
            if "clip_name2" in facial_restoration_workflow["160"]["inputs"]:
                params["clip_name2"] = facial_restoration_workflow["160"]["inputs"]["clip_name2"]
            print(f"从节点160提取CLIP模型")
        
        # 提取159节点参数（VAE模型）
        if "159" in facial_restoration_workflow and "inputs" in facial_restoration_workflow["159"]:
            if "vae_name" in facial_restoration_workflow["159"]["inputs"]:
                params["vae_name"] = facial_restoration_workflow["159"]["inputs"]["vae_name"]
                print(f"从节点159提取VAE模型: {params['vae_name']}")
            
    except Exception as e:
        print(f"提取面部修复参数时出错: {e}")
        import traceback
        traceback.print_exc()
    
    return params

def save_facial_restoration_workflow(params):
    workflow_copy = copy.deepcopy(facial_restoration_workflow)
    
    # 如果工作流为空，使用默认结构
    if not workflow_copy:
        logging.warning("面部修复工作流为空，无法保存参数")
        return workflow_copy
    
    try:
        # 更新303节点参数（图片命名）
        if "303" in workflow_copy:
            if "inputs" not in workflow_copy["303"]:
                workflow_copy["303"]["inputs"] = {}
            workflow_copy["303"]["inputs"]["string"] = params["image_name"]
            print(f"已将图片名称 '{params['image_name']}' 保存到面部修复工作流303节点")
        
        # 更新361节点参数（输入图像）
        if params.get("input_image") and "361" in workflow_copy:
            if "inputs" not in workflow_copy["361"]:
                workflow_copy["361"]["inputs"] = {}
            # ComfyUI期望的格式是直接使用图片名称，它会自动在input目录下查找
            # 确保只使用文件名，而不是完整路径
            if params["input_image"] and isinstance(params["input_image"], str):
                # 如果是路径，只获取文件名部分
                filename = os.path.basename(params["input_image"])
                workflow_copy["361"]["inputs"]["image"] = filename
                print(f"已将输入图像 {filename} 保存到面部修复工作流361节点")
            else:
                workflow_copy["361"]["inputs"]["image"] = params["input_image"]
                print(f"已将输入图像 {params['input_image']} 保存到面部修复工作流361节点")
        
        # 更新157节点参数（正向提示词）
        if "157" in workflow_copy:
            if "inputs" not in workflow_copy["157"]:
                workflow_copy["157"]["inputs"] = {}
            workflow_copy["157"]["inputs"]["text"] = params["positive_prompt"]
            print(f"已将正向提示词保存到面部修复工作流157节点")
        
        # 更新364节点参数（负向提示词）
        if "364" in workflow_copy:
            if "inputs" not in workflow_copy["364"]:
                workflow_copy["364"]["inputs"] = {}
            workflow_copy["364"]["inputs"]["text"] = params["negative_prompt"]
            print(f"已将负向提示词保存到面部修复工作流364节点")
            
        # 更新18节点参数（检测加载器）
        if "18" in workflow_copy:
            if "inputs" not in workflow_copy["18"]:
                workflow_copy["18"]["inputs"] = {}
            workflow_copy["18"]["inputs"]["model_name"] = params["bbox_model"]
            print(f"已将检测模型 {params['bbox_model']} 保存到面部修复工作流18节点")
        
        # 更新183节点参数（面部细化参数）
        if "183" in workflow_copy:
            if "inputs" not in workflow_copy["183"]:
                workflow_copy["183"]["inputs"] = {}
            
            # 更新面部细化参数
            face_detailer_params = ["guide_size", "guide_size_for", "max_size", "seed", "steps", "cfg", 
                                   "sampler_name", "scheduler", "denoise", "feather", "noise_mask", 
                                   "force_inpaint", "bbox_threshold", "bbox_dilation", "bbox_crop_factor",
                                   "sam_detection_hint", "sam_dilation", "sam_threshold", "sam_bbox_expansion", 
                                   "sam_mask_hint_threshold", "sam_mask_hint_use_negative", "drop_size", 
                                   "refiner_ratio", "cycle", "inpaint_model", "noise_mask_feather", 
                                   "tiled_encode", "tiled_decode"]
            
            for key in face_detailer_params:
                if key in params:
                    workflow_copy["183"]["inputs"][key] = params[key]
            
            print(f"已将面部细化参数保存到面部修复工作流183节点")
        
        # 更新161节点参数（UNET模型）
        if "161" in workflow_copy:
            if "inputs" not in workflow_copy["161"]:
                workflow_copy["161"]["inputs"] = {}
            workflow_copy["161"]["inputs"]["unet_name"] = params["unet_name"]
            print(f"已将UNET模型 {params['unet_name']} 保存到面部修复工作流161节点")
        
        # 更新160节点参数（CLIP模型）
        if "160" in workflow_copy:
            if "inputs" not in workflow_copy["160"]:
                workflow_copy["160"]["inputs"] = {}
            workflow_copy["160"]["inputs"]["clip_name1"] = params["clip_name1"]
            workflow_copy["160"]["inputs"]["clip_name2"] = params["clip_name2"]
            print(f"已将CLIP模型保存到面部修复工作流160节点")
        
        # 更新159节点参数（VAE模型）
        if "159" in workflow_copy:
            if "inputs" not in workflow_copy["159"]:
                workflow_copy["159"]["inputs"] = {}
            workflow_copy["159"]["inputs"]["vae_name"] = params["vae_name"]
            print(f"已将VAE模型 {params['vae_name']} 保存到面部修复工作流159节点")
        
        # 保存工作流文件
        save_facial_restoration_workflow_json(workflow_copy)
        print("已保存面部修复工作流")
        
        return workflow_copy
    except Exception as e:
        print(f"保存面部修复工作流参数时出错: {e}")
        import traceback
        traceback.print_exc()
        return workflow_copy

# 创建面部修复界面
with gr.Blocks(title="面部修复 - ComfyUI接口") as fr_demo:
    # 初始化工作流和参数
    facial_restoration_workflow = load_facial_restoration_workflow()
    facial_restoration_params = extract_facial_restoration_params()
    
    # 定义UI组件
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 面部修复")
            gr.Markdown("使用ComfyUI的面部修复功能，对图像中的人脸进行细化和修复")
    
    with gr.Row():
        with gr.Column(scale=5):
            # 左侧面板：图像上传和展示
            with gr.Group():
                gr.Markdown("### 图像上传和预览")
                
                with gr.Row():
                    fr_image_input = gr.Image(
                        type="pil",
                        label="上传要处理的图像",
                        height=512
                    )
                
                with gr.Row():
                    fr_open_input_folder_btn = gr.Button("打开输入文件夹")
                    fr_refresh_image_list_btn = gr.Button("刷新图像列表")
                
                with gr.Row():
                    fr_image_list = gr.Dropdown(
                        choices=get_input_folder_images(), 
                        label="选择ComfyUI输入文件夹中的图像",
                        interactive=True
                    )
                
                # 结果输出
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 完整处理图像")
                        fr_original_image_output = gr.Image(
                            type="pil",
                            label="完整处理图像（179节点）",
                            height=400,
                            interactive=False  # 设置为非交互式，即只读
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 面部细节图像")
                        fr_image_output = gr.Image(
                            type="pil",
                            label="面部细节图像（87节点）",
                            height=400,
                            interactive=False  # 设置为非交互式，即只读
                        )
                
                with gr.Row():
                    fr_open_output_folder_btn = gr.Button("打开输出文件夹")
                    fr_save_original_image_btn = gr.Button("保存完整处理图像（179节点）")
                    fr_save_processed_image_btn = gr.Button("保存面部细节图像（87节点）", variant="primary")
                    fr_status_text = gr.Markdown("准备就绪，请上传图像或选择现有图像进行处理")
        
        with gr.Column(scale=4):
            # 右侧面板：参数调整
            with gr.Group():
                gr.Markdown("### 处理参数")
                
                with gr.Accordion("基础参数", open=True):
                    with gr.Row():
                        fr_image_name = gr.Textbox(
                            label="输出文件名前缀",
                            value=facial_restoration_params["image_name"],
                            lines=1
                        )
                    
                    with gr.Row():
                        fr_seed = gr.Number(
                            label="随机种子",
                            value=facial_restoration_params["seed"],
                            precision=0
                        )
                        fr_random_seed_btn = gr.Button("随机种子", scale=1)
                    
                    with gr.Row():
                        fr_steps = gr.Slider(
                            label="采样步数",
                            minimum=1,
                            maximum=50,
                            value=facial_restoration_params["steps"],
                            step=1
                        )
                    
                    with gr.Row():
                        fr_cfg = gr.Slider(
                            label="CFG缩放",
                            minimum=0,
                            maximum=20,
                            value=facial_restoration_params["cfg"],
                            step=0.1
                        )
                    
                    with gr.Row():
                        fr_denoise = gr.Slider(
                            label="去噪强度",
                            minimum=0,
                            maximum=1,
                            value=facial_restoration_params["denoise"],
                            step=0.01
                        )
                    
                    with gr.Row():
                        fr_sampler_list = ["dpmpp_sde", "dpmpp_2m", "dpmpp_2m_sde", "ddim", "euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", "dpm_fast", "dpm_adaptive", "deis"]
                        fr_sampler_name = gr.Dropdown(
                            label="采样器",
                            choices=fr_sampler_list,
                            value=facial_restoration_params["sampler_name"]
                        )
                    
                    with gr.Row():
                        fr_scheduler_list = ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform", "logSNR", "sgm_logarithmic", "beta"]
                        fr_scheduler = gr.Dropdown(
                            label="调度器",
                            choices=fr_scheduler_list,
                            value=facial_restoration_params["scheduler"]
                        )
                
                with gr.Accordion("面部细化参数", open=True):
                    with gr.Row():
                        fr_guide_size = gr.Slider(
                            label="指导尺寸",
                            minimum=256,
                            maximum=1024,
                            value=facial_restoration_params["guide_size"],
                            step=64
                        )
                    
                    with gr.Row():
                        fr_max_size = gr.Slider(
                            label="最大尺寸",
                            minimum=512,
                            maximum=2048,
                            value=facial_restoration_params["max_size"],
                            step=64
                        )
                    
                    with gr.Row():
                        fr_feather = gr.Slider(
                            label="羽化",
                            minimum=0,
                            maximum=50,
                            value=facial_restoration_params["feather"],
                            step=1
                        )
                    
                    with gr.Row():
                        fr_bbox_threshold = gr.Slider(
                            label="检测阈值",
                            minimum=0.1,
                            maximum=1.0,
                            value=facial_restoration_params["bbox_threshold"],
                            step=0.05
                        )
                    
                    with gr.Row():
                        fr_bbox_dilation = gr.Slider(
                            label="边界框扩张",
                            minimum=0,
                            maximum=100,
                            value=facial_restoration_params["bbox_dilation"],
                            step=1
                        )
                    
                    with gr.Row():
                        fr_bbox_crop_factor = gr.Slider(
                            label="边界框裁剪因子",
                            minimum=1,
                            maximum=10,
                            value=facial_restoration_params["bbox_crop_factor"],
                            step=0.1
                        )
                    
                    with gr.Row():
                        fr_guide_size_for = gr.Checkbox(
                            label="使用指导尺寸",
                            value=facial_restoration_params["guide_size_for"]
                        )
                        fr_noise_mask = gr.Checkbox(
                            label="噪声遮罩",
                            value=facial_restoration_params["noise_mask"]
                        )
                        fr_force_inpaint = gr.Checkbox(
                            label="强制修复",
                            value=facial_restoration_params["force_inpaint"]
                        )
                
                with gr.Accordion("高级参数", open=True):
                    # 获取模型列表
                    models_dict = get_models_list()
                    
                    # 添加刷新模型列表的按钮和函数
                    def refresh_model_lists():
                        models = get_models_list()
                        return (
                            gr.update(choices=models["ultralytics"], value=facial_restoration_params["bbox_model"]),
                            gr.update(choices=models["unet"], value=facial_restoration_params["unet_name"]),
                            gr.update(choices=models["clip"], value=facial_restoration_params["clip_name1"]),
                            gr.update(choices=models["clip"], value=facial_restoration_params["clip_name2"]),
                            gr.update(choices=models["vae"], value=facial_restoration_params["vae_name"]),
                            "模型列表已刷新"
                        )

                    fr_refresh_models_btn = gr.Button("刷新模型列表")
                    fr_refresh_status = gr.Textbox(label="状态", value="", visible=False)
                    
                    with gr.Row():
                        fr_bbox_model = gr.Dropdown(
                            label="检测模型",
                            choices=models_dict["ultralytics"],
                            value=facial_restoration_params["bbox_model"],
                            allow_custom_value=True
                        )
                    
                    with gr.Row():
                        fr_unet_name = gr.Dropdown(
                            label="UNET模型",
                            choices=models_dict["unet"],
                            value=facial_restoration_params["unet_name"],
                            allow_custom_value=True
                        )
                    
                    with gr.Row():
                        fr_clip_name1 = gr.Dropdown(
                            label="CLIP模型1",
                            choices=models_dict["clip"],
                            value=facial_restoration_params["clip_name1"],
                            allow_custom_value=True
                        )
                    
                    with gr.Row():
                        fr_clip_name2 = gr.Dropdown(
                            label="CLIP模型2",
                            choices=models_dict["clip"],
                            value=facial_restoration_params["clip_name2"],
                            allow_custom_value=True
                        )
                    
                    with gr.Row():
                        fr_vae_name = gr.Dropdown(
                            label="VAE模型",
                            choices=models_dict["vae"],
                            value=facial_restoration_params["vae_name"],
                            allow_custom_value=True
                        )
                    
                    fr_refresh_models_btn.click(
                        fn=refresh_model_lists, 
                        inputs=[], 
                        outputs=[fr_bbox_model, fr_unet_name, fr_clip_name1, fr_clip_name2, fr_vae_name, fr_refresh_status]
                    )
                
                with gr.Accordion("提示词", open=True):
                    with gr.Row():
                        fr_positive_prompt = gr.Textbox(
                            label="正向提示词",
                            value=facial_restoration_params["positive_prompt"],
                            lines=3
                        )
                    
                    with gr.Row():
                        fr_negative_prompt = gr.Textbox(
                            label="负向提示词",
                            value=facial_restoration_params["negative_prompt"],
                            lines=2
                        )
                
                # 生成按钮
                with gr.Row():
                    fr_generate_btn = gr.Button("开始面部修复", variant="primary")
    
    # 定义所有输入参数列表
    fr_all_inputs = [
        fr_image_input,
        fr_image_name,
        fr_positive_prompt,
        fr_negative_prompt,
        fr_steps,
        fr_cfg,
        fr_sampler_name,
        fr_scheduler,
        fr_denoise,
        fr_guide_size,
        fr_max_size,
        fr_feather,
        fr_noise_mask,
        fr_force_inpaint,
        fr_bbox_threshold,
        fr_bbox_dilation,
        fr_bbox_crop_factor,
        fr_guide_size_for,
        fr_seed,
        fr_bbox_model,
        fr_unet_name,
        fr_clip_name1,
        fr_clip_name2,
        fr_vae_name
    ]
    
    # 定义图像处理函数
    def save_fr_image_to_input_folder(img):
        if img is None:
            return None, "未选择图像", []
        
        # 确保ComfyUI的input文件夹存在
        os.makedirs(os.path.join(WSL_COMFYUI_PATH, "input"), exist_ok=True)
        
        # 生成随机文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = random.randint(1000, 9999)
        filename = f"fr_input_{timestamp}_{random_suffix}.png"
        filepath = os.path.join(WSL_COMFYUI_PATH, "input", filename)
        
        # 保存图像
        img.save(filepath)
        print(f"已保存图像到: {filepath}")
        
        # 刷新图像列表
        updated_choices = get_input_folder_images()
        
        return filename, f"图像已保存到: {filepath}", updated_choices
    
    # 打开输入文件夹
    def open_fr_input_folder():
        # 确保ComfyUI的input文件夹存在
        comfyui_input_path = os.path.join(WSL_COMFYUI_PATH, "input")
        os.makedirs(comfyui_input_path, exist_ok=True)
        
        # 根据操作系统打开文件夹
        if platform.system() == "Windows":
            # 直接使用WSL路径打开，不转换为本地路径
            os.system(f'explorer "{comfyui_input_path}"')
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", os.path.abspath(comfyui_input_path)])
        else:  # Linux
            subprocess.run(["xdg-open", os.path.abspath(comfyui_input_path)])
        
        return f"已打开输入文件夹: {comfyui_input_path}"
    
    # 选择现有图像
    def select_existing_fr_image(file_path):
        if not file_path:
            return None, "未选择图像"
        
        try:
            # 构建完整路径
            full_path = os.path.join(WSL_COMFYUI_PATH, "input", file_path)
            
            # 加载图像
            img = Image.open(full_path)
            print(f"已加载图像: {full_path}")
            
            return img, f"已加载图像: {file_path}"
        except Exception as e:
            print(f"加载图像时出错: {e}")
            return None, f"加载图像时出错: {str(e)}"
    
    # 刷新图像列表
    def refresh_fr_image_list():
        new_images = get_input_folder_images()
        new_choices = []
        for name in new_images:
            try:
                full_path = os.path.join(WSL_COMFYUI_PATH, "input", name)
                new_choices.append(name)
            except Exception as e:
                print(f"刷新面部修复图片列表时出错: {e}")
        fr_image_list.choices = new_choices
        return None
    
    # 打开输出文件夹
    def open_output_folder_fr():
        # 确保output文件夹存在
        os.makedirs("output", exist_ok=True)
        
        # 获取绝对路径
        output_folder = os.path.abspath("output")
        
        # 根据操作系统打开文件夹
        if platform.system() == "Windows":
            os.startfile(output_folder)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", output_folder])
        else:  # Linux
            subprocess.run(["xdg-open", output_folder])
        
        return "已打开输出文件夹"
    
    # 生成函数
    def generate_facial_restoration(*args, progress=gr.Progress()):
        # 将参数转换为字典
        fr_image_input = args[0]
        
        # 检查是否提供了图像
        if fr_image_input is None:
            return None, None, "错误：请先上传或选择一张图像"
        
        # 保存图像到输入文件夹
        progress(0.02, "保存输入图像...")
        image_filename, _, _ = save_fr_image_to_input_folder(fr_image_input)
        
        # 更新参数
        updated_params = facial_restoration_params.copy()
        updated_params["image_name"] = args[1]
        updated_params["positive_prompt"] = args[2]
        updated_params["negative_prompt"] = args[3]
        updated_params["steps"] = args[4]
        updated_params["cfg"] = args[5]
        updated_params["sampler_name"] = args[6]
        updated_params["scheduler"] = args[7]
        updated_params["denoise"] = args[8]
        updated_params["guide_size"] = args[9]
        updated_params["max_size"] = args[10]
        updated_params["feather"] = args[11]
        updated_params["noise_mask"] = args[12]
        updated_params["force_inpaint"] = args[13]
        updated_params["bbox_threshold"] = args[14]
        updated_params["bbox_dilation"] = args[15]
        updated_params["bbox_crop_factor"] = args[16]
        updated_params["guide_size_for"] = args[17]
        updated_params["seed"] = args[18]
        updated_params["bbox_model"] = args[19]
        updated_params["unet_name"] = args[20]
        updated_params["clip_name1"] = args[21]
        updated_params["clip_name2"] = args[22]
        updated_params["vae_name"] = args[23]
        updated_params["input_image"] = image_filename
        
        # 保存参数到JSON文件
        progress(0.05, "保存参数到配置文件...")
        saved_workflow = save_facial_restoration_workflow(updated_params)
        
        # 创建状态更新的函数
        status_text = "图像生成完成！"
        is_completed = False
        complete_image = None
        detail_image = None
        
        def progress_callback(value, message):
            nonlocal status_text, is_completed
            status_text = message
            progress(value, message)
            print(f"UI进度更新: {value:.2f} - {message}")
            
            # 当进度达到0.95时，增加提示信息
            if value >= 0.95 and not is_completed:
                status_text = "完成工作流执行，正在寻找并合成最终图像，请耐心等待..."
                progress(0.95, status_text)
                print("面部修复工作流执行接近完成，正在等待最终图像合成...")
        
        # 发送工作流到ComfyUI并获取生成结果
        try:
            # 尝试获取两种图像结果
            result_images = send_workflow_to_comfyui(saved_workflow, progress_callback, return_all_images=True)
            is_completed = True
            
            # 检查是否成功获取图像
            if result_images and len(result_images) >= 2:
                complete_image = result_images[0]  # 179节点的完整图像
                detail_image = result_images[1]    # 87节点的面部细节图像
                status_text = "图像生成完成！"
                progress(1.0, "完成")
            elif result_images and len(result_images) == 1:
                # 如果只获取到一张图像，同时设置为两个输出
                complete_image = result_images[0]
                detail_image = result_images[0]
                status_text = "仅获取到一张处理图像"
                progress(1.0, "完成")
            else:
                # 如果没有获取到图像，尝试查找最新的图像
                print("未找到生成的图像，尝试查找最新保存的图像...")
                status_text = "未找到生成的图像，尝试查找最新保存的图像..."
                progress(0.95, status_text)
                
                latest_image = find_latest_image()
                if latest_image:
                    complete_image = latest_image
                    detail_image = latest_image
                    status_text = "已找到最新保存的图像"
                    progress(1.0, "完成")
                else:
                    status_text = "未能找到任何生成的图像"
                    progress(1.0, "完成")
        except Exception as e:
            print(f"生成图像过程中出错: {e}")
            import traceback
            traceback.print_exc()
            status_text = f"生成图像失败: {str(e)}"
            is_completed = True
            # 尝试查找最新的图像作为备选
            latest_image = find_latest_image()
            if latest_image:
                complete_image = latest_image
                detail_image = latest_image
        
        # 返回生成的图像和原始图像
        return complete_image, detail_image, status_text
    
    # 随机种子按钮的点击事件
    fr_random_seed_btn.click(fn=generate_random_seed, inputs=None, outputs=fr_seed)
    
    # 生成按钮的点击事件
    fr_generate_btn.click(
        fn=generate_facial_restoration, 
        inputs=fr_all_inputs, 
        outputs=[fr_original_image_output, fr_image_output, fr_status_text],
        show_progress="full"
    )
    
    # 图像列表相关事件
    fr_image_list.change(
        fn=select_existing_fr_image,
        inputs=fr_image_list,
        outputs=[fr_image_input, fr_status_text]
    )
    
    # 上传图像后自动显示在原始图像框中
    def handle_fr_image_upload(img):
        filename, status_text, updated_choices = save_fr_image_to_input_folder(img)
        # updated_choices已经是正确的格式，直接赋值
        fr_image_list.choices = updated_choices
        fr_image_list.value = filename
        return img, status_text

    fr_image_input.upload(
        fn=handle_fr_image_upload,
        inputs=fr_image_input,
        outputs=[fr_image_input, fr_status_text]
    )
    
    # 按钮点击事件
    fr_open_input_folder_btn.click(
        fn=open_fr_input_folder,
        inputs=None,
        outputs=fr_status_text
    )
    
    fr_refresh_image_list_btn.click(
        fn=refresh_fr_image_list,
        inputs=None,
        outputs=None
    )
    
    fr_open_output_folder_btn.click(
        fn=open_output_folder_fr,
        inputs=None,
        outputs=fr_status_text
    )

    # 选择现有图像时更新输入区域图像
    def select_existing_fr_image_with_preview(file_path):
        if not file_path:
            return None, "未选择图像"
        
        try:
            # 构建完整路径 - file_path现在就是文件名
            full_path = os.path.join(WSL_COMFYUI_PATH, "input", file_path)
            
            # 加载图像
            img = Image.open(full_path)
            print(f"已加载图像: {full_path}")
            
            return img, f"已加载图像: {file_path}"
        except Exception as e:
            print(f"加载图像时出错: {e}")
            return None, f"加载图像时出错: {str(e)}"
    
    # 图像列表选择事件
    fr_image_list.change(
        fn=select_existing_fr_image_with_preview,
        inputs=fr_image_list,
        outputs=[fr_image_input, fr_status_text]
    )

    # 保存当前处理后图像（对应87号节点）
    def save_current_fr_processed_image(image):
        if image is None:
            return "错误：没有可保存的面部细节图像"
        
        try:
            # 确保output文件夹存在
            os.makedirs("output", exist_ok=True)
            
            # 使用时间戳生成文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facial_restoration_detail_{timestamp}.png"
            filepath = os.path.join("output", filename)
            
            # 保存图像
            image.save(filepath)
            print(f"已保存面部细节图像到: {filepath}")
            
            return f"面部细节图像已保存到: {filepath}"
        except Exception as e:
            print(f"保存图像时出错: {e}")
            return f"保存图像失败: {str(e)}"
    
    # 保存完整处理图像（对应179号节点）
    def save_current_fr_original_image(image):
        if image is None:
            return "错误：没有可保存的完整处理图像"
        
        try:
            # 确保output文件夹存在
            os.makedirs("output", exist_ok=True)
            
            # 使用时间戳生成文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facial_restoration_complete_{timestamp}.png"
            filepath = os.path.join("output", filename)
            
            # 保存图像
            image.save(filepath)
            print(f"已保存完整处理图像到: {filepath}")
            
            return f"完整处理图像已保存到: {filepath}"
        except Exception as e:
            print(f"保存图像时出错: {e}")
            return f"保存图像失败: {str(e)}"

    fr_save_processed_image_btn.click(
        fn=save_current_fr_processed_image,
        inputs=fr_image_output,
        outputs=fr_status_text
    )
    
    fr_save_original_image_btn.click(
        fn=save_current_fr_original_image,
        inputs=fr_original_image_output,
        outputs=fr_status_text
    )

# 启动服务器，设置端口为5555，路径为/ttoi，允许内网访问(share=True)
if __name__ == "__main__":
    try:
        # 记录一些环境信息
        logging.info("正在启动Gradio服务器...")
        logging.info(f"服务器配置: 文生图端口=5555, 图生图端口=5556, 三视图端口=5557, 放大及面部修复端口=5558, 面部修复端口=5559")
        
        # 检查是否处于打包环境
        if getattr(sys, 'frozen', False):
            print(f"运行环境: 打包后的EXE")
            print(f"EXE路径: {sys.executable}")
            print(f"EXE目录: {os.path.dirname(sys.executable)}")
            logging.info(f"运行环境: 打包后的EXE")
            logging.info(f"EXE路径: {sys.executable}")
            logging.info(f"EXE目录: {os.path.dirname(sys.executable)}")
            
            # 添加额外检查
            try:
                import gradio_client
                logging.info(f"gradio_client版本: {gradio_client.__version__}")
                logging.info(f"gradio_client路径: {os.path.dirname(gradio_client.__file__)}")
                # 检查types.json是否存在
                types_json_path = os.path.join(os.path.dirname(gradio_client.__file__), "types.json")
                if os.path.exists(types_json_path):
                    logging.info(f"types.json文件存在: {types_json_path}")
                else:
                    logging.error(f"types.json文件不存在: {types_json_path}")
                    print(f"ERROR: types.json文件不存在: {types_json_path}")
            except Exception as e:
                logging.error(f"检查gradio_client时出错: {e}")
        else:
            logging.info("运行环境: 开发环境")
        
        # 确保必要的目录存在
        os.makedirs("json", exist_ok=True)
        os.makedirs("workflows", exist_ok=True)
        os.makedirs("output", exist_ok=True)
        os.makedirs("input", exist_ok=True)  # 确保input文件夹存在
        
        # 检查json目录和workflows.json文件
        if not os.path.exists("json/workflows.json"):
            logging.warning("workflows.json文件不存在")
            # 检查exe目录下是否有json/workflows.json
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                if os.path.exists(os.path.join(exe_dir, "json/workflows.json")):
                    logging.info("在exe目录下找到workflows.json文件")
                    # 复制workflows.json到当前目录
                    shutil.copy2(
                        os.path.join(exe_dir, "json/workflows.json"),
                        "json/workflows.json"
                    )
                    logging.info("已复制workflows.json到当前目录")
        
        # 检查图生图工作流文件
        if not os.path.exists("workflows/img_to_img.json"):
            logging.warning("img_to_img.json文件不存在")
            # 检查exe目录下是否有workflows/img_to_img.json
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                if os.path.exists(os.path.join(exe_dir, "workflows/img_to_img.json")):
                    logging.info("在exe目录下找到img_to_img.json文件")
                    # 复制img_to_img.json到当前目录
                    shutil.copy2(
                        os.path.join(exe_dir, "workflows/img_to_img.json"),
                        "workflows/img_to_img.json"
                    )
                    logging.info("已复制img_to_img.json到当前目录")
                    
        # 检查三视图工作流文件
        if not os.path.exists("workflows/Random_three_views.json"):
            logging.warning("Random_three_views.json文件不存在")
            # 检查exe目录下是否有workflows/Random_three_views.json
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                if os.path.exists(os.path.join(exe_dir, "workflows/Random_three_views.json")):
                    logging.info("在exe目录下找到Random_three_views.json文件")
                    # 复制Random_three_views.json到当前目录
                    shutil.copy2(
                        os.path.join(exe_dir, "workflows/Random_three_views.json"),
                        "workflows/Random_three_views.json"
                    )
                    logging.info("已复制Random_three_views.json到当前目录")
        
        # 检查放大及面部修复工作流文件
        if not os.path.exists("workflows/Magnified_facial_restoration.json"):
            logging.warning("Magnified_facial_restoration.json文件不存在")
            # 检查exe目录下是否有workflows/Magnified_facial_restoration.json
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                if os.path.exists(os.path.join(exe_dir, "workflows/Magnified_facial_restoration.json")):
                    logging.info("在exe目录下找到Magnified_facial_restoration.json文件")
                    # 复制Magnified_facial_restoration.json到当前目录
                    shutil.copy2(
                        os.path.join(exe_dir, "workflows/Magnified_facial_restoration.json"),
                        "workflows/Magnified_facial_restoration.json"
                    )
                    logging.info("已复制Magnified_facial_restoration.json到当前目录")
        
        # 检查面部修复工作流文件
        if not os.path.exists("workflows/Facial_restoration.json"):
            logging.warning("Facial_restoration.json文件不存在")
            # 检查exe目录下是否有workflows/Facial_restoration.json
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                if os.path.exists(os.path.join(exe_dir, "workflows/Facial_restoration.json")):
                    logging.info("在exe目录下找到Facial_restoration.json文件")
                    # 复制Facial_restoration.json到当前目录
                    shutil.copy2(
                        os.path.join(exe_dir, "workflows/Facial_restoration.json"),
                        "workflows/Facial_restoration.json"
                    )
                    logging.info("已复制Facial_restoration.json到当前目录")

        # 使用多线程启动三个独立的Gradio应用
        import threading

        def run_txt2img():
            # 设置文生图界面标题
            txt2img_demo.title = "文生图 - ComfyUI接口"
            txt2img_demo.launch(
                server_name="127.0.0.1",  # 仅允许本地访问
                server_port=5555,
                share=False,  # 关闭外网访问
                allowed_paths=["output", "input", WSL_COMFYUI_PATH, os.path.join(WSL_COMFYUI_PATH, "input")]  # 添加WSL路径到允许路径
            )

        def run_img2img():
            # 设置图生图界面标题
            img2img_demo.title = "图生图 - ComfyUI接口"
            img2img_demo.launch(
                server_name="127.0.0.1",  # 仅允许本地访问
                server_port=5556,
                share=False,  # 关闭外网访问
                allowed_paths=["output", "input", WSL_COMFYUI_PATH, os.path.join(WSL_COMFYUI_PATH, "input")]  # 添加WSL路径到允许路径
            )
            
        def run_rtv():
            # 设置三视图界面标题
            random_three_views_demo.title = "三视图 - ComfyUI接口"
            random_three_views_demo.launch(
                server_name="127.0.0.1",  # 仅允许本地访问
                server_port=5557,
                share=False,  # 关闭外网访问
                allowed_paths=["output", "input", WSL_COMFYUI_PATH, os.path.join(WSL_COMFYUI_PATH, "input")]  # 添加WSL路径到允许路径
            )

        def run_mfr():
            # 设置放大及面部修复界面标题
            magnified_facial_restoration_demo.title = "放大及面部修复 - ComfyUI接口"
            magnified_facial_restoration_demo.launch(
                server_name="127.0.0.1",  # 仅允许本地访问
                server_port=5558,
                share=False,  # 关闭外网访问
                allowed_paths=["output", "input", WSL_COMFYUI_PATH, os.path.join(WSL_COMFYUI_PATH, "input")]  # 添加WSL路径到允许路径
            )
            
        def run_fr():
            # 设置面部修复界面标题
            fr_demo.title = "面部修复 - ComfyUI接口"
            fr_demo.launch(
                server_name="127.0.0.1",  # 仅允许本地访问
                server_port=5559,
                share=False,  # 关闭外网访问
                allowed_paths=["output", "input", WSL_COMFYUI_PATH, os.path.join(WSL_COMFYUI_PATH, "input")]  # 添加WSL路径到允许路径
            )

        # 创建并启动线程
        print("启动文生图服务（端口5555）...")
        t1 = threading.Thread(target=run_txt2img)
        t1.daemon = True
        t1.start()

        print("启动图生图服务（端口5556）...")
        t2 = threading.Thread(target=run_img2img)
        t2.daemon = True
        t2.start()
        
        print("启动三视图服务（端口5557）...")
        t3 = threading.Thread(target=run_rtv)
        t3.daemon = True
        t3.start()

        print("启动放大及面部修复服务（端口5558）...")
        t4 = threading.Thread(target=run_mfr)
        t4.daemon = True
        t4.start()
        
        print("启动面部修复服务（端口5559）...")
        t5 = threading.Thread(target=run_fr)
        t5.daemon = True
        t5.start()

        # 打印访问地址
        print("\n====== 服务已启动，请通过以下地址访问 ======")
        print("文生图: http://127.0.0.1:5555")
        print("图生图: http://127.0.0.1:5556")
        print("三视图: http://127.0.0.1:5557")
        print("放大及面部修复: http://127.0.0.1:5558")
        print("面部修复: http://127.0.0.1:5559")
        print("===========================================\n")

        # 保持主线程运行，防止程序退出
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("程序被用户中断")

    except Exception as e:
        logging.error(f"启动服务器时出错: {str(e)}")
        logging.error(traceback.format_exc())
        # 如果是打包后的exe，保持窗口不关闭，便于查看错误
        if getattr(sys, 'frozen', False):
            print(f"启动出错: {str(e)}")
            print("详细错误信息已记录到日志文件: ttoi_error.log")
            input("按Enter键退出...")
        raise
