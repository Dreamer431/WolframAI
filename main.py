import os
from dotenv import load_dotenv
import wolframalpha
import gradio as gr
from langchain_community.utilities import WolframAlphaAPIWrapper
from langchain.llms import OpenAI  # 可选：用于结果后处理
import openai
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wolfram_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 加载环境变量（在.env文件中存放APP_ID）
load_dotenv()
logger.info("环境变量已加载")

# 初始化Wolfram Alpha客户端
def init_wolfram():
    app_id = os.getenv("WOLFRAM_ALPHA_APPID")
    if not app_id:
        raise ValueError("请将WOLFRAM_ALPHA_APPID添加到.env文件")
    return wolframalpha.Client(app_id)

# DeepSeek翻译函数
def translate_to_english(text):
    # 简单检测是否可能是英文（如果包含足够的英文字符）
    english_char_ratio = len(re.findall(r'[a-zA-Z]', text)) / len(text) if len(text) > 0 else 0
    # 如果英文字符占比超过50%，认为是英文，不需要翻译
    if english_char_ratio > 0.5:
        logger.info("检测到输入已经是英文，跳过翻译")
        return text
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.warning("未找到DEEPSEEK_API_KEY，将不进行翻译")
        return text  # 没有key就直接返回原文
    try:
        logger.info(f"翻译中文到英文: {text[:30]}...")
        # 创建OpenAI客户端（适用于OpenAI 1.0+版本）
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"  # DeepSeek API地址
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a translation assistant. Translate the Chinese text to English. Return only the translation without any additional text or explanation. No introduction or conclusion."},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=256
        )
        result = response.choices[0].message.content.strip()
        logger.info(f"翻译结果: {result[:30]}...")
        return result
    except Exception as e:
        logger.error(f"翻译到英文失败: {str(e)}")
        return text  # 翻译失败时直接返回原文

# 将英文结果翻译回中文
def translate_to_chinese(text):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return text  # 没有key就直接返回原文
    try:
        # 创建OpenAI客户端（适用于OpenAI 1.0+版本）
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"  # DeepSeek API地址
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a translation assistant. Translate the English text to Chinese. Return only the translation without any additional text or explanation. No introduction or conclusion."},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=512
        )
        translated = response.choices[0].message.content.strip()
        # 将翻译结果加上原始英文（在{}中）
        result = f"{translated} {{英文原文: {text}}}"
        return result
    except Exception as e:
        logger.error(f"翻译到中文失败: {str(e)}")
        return text  # 翻译失败时直接返回原文

# 创建交互界面
def create_interface():
    with gr.Blocks() as demo:
        gr.Markdown("## Wolfram Alpha 知识引擎问答系统")
        
        # 添加翻译设置
        with gr.Row():
            enable_translation = gr.Checkbox(label="启用中英文自动翻译", value=True, 
                                           info="打开后可使用中文输入问题并获得中文回答，关闭后需使用英文")
            translation_status = gr.Markdown("✅ 已启用翻译：可以使用中文提问")
        
        def update_translation_status(enabled):
            if enabled:
                return "✅ 已启用翻译：可以使用中文提问"
            else:
                return "❗ 已关闭翻译：请使用英文提问，回答将保持英文原文"
        
        enable_translation.change(update_translation_status, inputs=enable_translation, outputs=translation_status)
        
        # 修改查询函数以支持翻译开关
        def raw_query_with_translation(query, enable_trans):
            logger.info(f"接收原始查询: {query}, 翻译开关: {enable_trans}")
            client = init_wolfram()
            try:
                # 根据开关决定是否翻译
                if enable_trans:
                    query_en = translate_to_english(query)
                    logger.info(f"翻译后的查询: {query_en}")
                else:
                    query_en = query
                    logger.info(f"不进行翻译，直接使用原始查询: {query_en}")
                
                res = client.query(query_en)
                result = next(res.results).text  # 获取第一个结果
                logger.info(f"Wolfram Alpha原始结果: {result[:50]}...")
                
                # 根据开关决定是否将结果翻译回中文
                if enable_trans:
                    translated = translate_to_chinese(result)
                    logger.info(f"翻译回中文后的结果: {translated[:50]}...")
                    return translated
                else:
                    logger.info(f"不进行翻译，直接返回原始结果")
                    return result
            except Exception as e:
                error_msg = f"查询失败: {str(e)}"
                logger.error(error_msg)
                return error_msg
        
        def enhanced_query_with_translation(query, enable_trans):
            logger.info(f"接收增强查询: {query}, 翻译开关: {enable_trans}")
            # 获取APP_ID并初始化WolframAlphaAPIWrapper
            app_id = os.getenv("WOLFRAM_ALPHA_APPID")
            if not app_id:
                error_msg = "错误：未找到WOLFRAM_ALPHA_APPID环境变量"
                logger.error(error_msg)
                return error_msg
            
            logger.info(f"使用APP_ID: {app_id[:5]}***初始化WolframAlphaAPIWrapper")
            wolfram = WolframAlphaAPIWrapper(wolfram_alpha_appid=app_id)
            try:
                # 根据开关决定是否翻译
                if enable_trans:
                    query_en = translate_to_english(query)
                    logger.info(f"翻译后的查询: {query_en}")
                else:
                    query_en = query
                    logger.info(f"不进行翻译，直接使用原始查询: {query_en}")
                
                # 尝试直接使用Wolfram Alpha回答
                logger.info("发送查询到Wolfram Alpha")
                direct_result = wolfram.run(query_en)
                logger.info(f"Wolfram Alpha直接结果: {direct_result[:50]}...")
                
                # 检查Wolfram Alpha是否无法回答问题
                no_answer_phrases = [
                    "Wolfram Alpha wasn't able to answer it",
                    "Wolfram Alpha cannot", "Wolfram Alpha doesn't", "Wolfram Alpha does not", 
                    "I don't know", "I don't have", "I cannot", "No information", 
                    "cannot answer", "unable to", "doesn't know", "does not know",
                    "couldn't find", "could not find", "couldn't understand", "could not understand"
                ]
                
                wolfram_failed = any(phrase in direct_result.lower() for phrase in no_answer_phrases)
                
                # 如果Wolfram Alpha能直接回答，就使用其结果
                if not wolfram_failed:
                    logger.info("Wolfram Alpha能直接回答问题")
                    result = direct_result
                else:
                    # 如果Wolfram Alpha无法直接回答，使用问题拆解策略
                    logger.info("Wolfram Alpha无法直接回答，开始问题拆解策略")
                    api_key = os.getenv("DEEPSEEK_API_KEY")
                    if not api_key:
                        return f"错误：Wolfram Alpha无法回答此问题，且未找到DEEPSEEK_API_KEY，无法使用问题拆解策略。"
                        
                    # 步骤1：使用DeepSeek将问题拆解成Wolfram Alpha可以回答的子问题
                    logger.info("步骤1：使用DeepSeek拆解问题")
                    client = openai.OpenAI(
                        api_key=api_key,
                        base_url="https://api.deepseek.com/v1"
                    )
                    
                    decompose_response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "你是一个问题分析专家。你的任务是将复杂问题拆解为Wolfram Alpha能回答的简单子问题。Wolfram Alpha擅长回答数学计算、科学事实、地理信息、日期和时间等具体问题。\n\n请将用户问题拆解为2-5个独立的子问题，以便于Wolfram Alpha回答。每个子问题应该是清晰、具体、独立的。\n\n输出格式要求：\n1. 子问题一\n2. 子问题二\n...\n\n只需要输出子问题列表，不要有任何其他说明或解释。"},
                            {"role": "user", "content": query_en}
                        ],
                        temperature=0.3,
                        max_tokens=512
                    )
                    
                    sub_questions_text = decompose_response.choices[0].message.content.strip()
                    logger.info(f"子问题列表: {sub_questions_text}")
                    
                    # 提取子问题列表
                    sub_questions = []
                    for line in sub_questions_text.split('\n'):
                        line = line.strip()
                        if re.match(r'^\d+\.', line):  # 匹配"1."，"2."等开头的行
                            question = re.sub(r'^\d+\.\s*', '', line)  # 移除行首的序号
                            if question:
                                sub_questions.append(question)
                    
                    if not sub_questions:
                        # 可能DeepSeek没有按照预期格式输出，尝试直接分割文本
                        sub_questions = [q.strip() for q in sub_questions_text.split('\n') if q.strip()]
                        
                    logger.info(f"提取的子问题数量: {len(sub_questions)}")
                    
                    if not sub_questions:
                        # 如果子问题为空，使用备用回答方式
                        logger.info("未能成功拆解问题，使用DeepSeek直接回答")
                        direct_response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "You are a helpful assistant that provides factual information. Answer the user's question with accurate information. If you don't know the answer, clearly state that you don't know."},
                                {"role": "user", "content": f"Please answer this question as accurately as possible: {query_en}"}
                            ],
                            temperature=0.3,
                            max_tokens=1024
                        )
                        result = f"[DeepSeek直接回答] {direct_response.choices[0].message.content.strip()}"
                    else:
                        # 步骤2：逐个向Wolfram Alpha提问并收集回答
                        logger.info("步骤2：向Wolfram Alpha提交子问题")
                        sub_answers = []
                        
                        for i, sub_q in enumerate(sub_questions):
                            logger.info(f"提交子问题 {i+1}/{len(sub_questions)}: {sub_q}")
                            try:
                                sub_answer = wolfram.run(sub_q)
                                sub_answers.append(f"问题 {i+1}: {sub_q}\n回答: {sub_answer}")
                                logger.info(f"得到子问题 {i+1} 的回答: {sub_answer[:50]}...")
                            except Exception as e:
                                error = f"无法回答子问题 {i+1}: {str(e)}"
                                sub_answers.append(f"问题 {i+1}: {sub_q}\n回答: {error}")
                                logger.error(error)
                        
                        # 步骤3：使用DeepSeek整合子问题的回答
                        logger.info("步骤3：整合所有子问题的回答")
                        all_sub_answers = "\n\n".join(sub_answers)
                        
                        combine_response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "你是一个信息整合专家。你的任务是根据提供的子问题和答案，生成一个综合性的、有条理的回答。你的回答应该完整解答用户的问题，并保持逻辑清晰、内容准确。"},
                                {"role": "user", "content": f"原始问题: {query_en}\n\n以下是子问题和它们的回答：\n\n{all_sub_answers}\n\n请整合以上信息，给出原始问题的完整回答。"}
                            ],
                            temperature=0.3,
                            max_tokens=1024
                        )
                        
                        combined_answer = combine_response.choices[0].message.content.strip()
                        logger.info(f"整合后的最终答案: {combined_answer[:50]}...")
                        
                        # 完整结果
                        result = f"[问题拆解回答]\n{combined_answer}"
                
                # 使用DeepSeek优化Wolfram Alpha的原始答案
                if not result.startswith('[问题拆解回答]') and not result.startswith('[DeepSeek直接回答]'):
                    api_key = os.getenv("DEEPSEEK_API_KEY")
                    if api_key:
                        try:
                            logger.info("使用DeepSeek优化答案")
                            client = openai.OpenAI(
                                api_key=api_key,
                                base_url="https://api.deepseek.com/v1"  # DeepSeek API地址
                            )
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant that explains complex information clearly."},
                                    {"role": "user", "content": f"将以下Wolfram Alpha的原始答案转换为更自然、易于理解的语言：\n{result}"}
                                ],
                                temperature=0.3,
                                max_tokens=512
                            )
                            result = response.choices[0].message.content.strip()
                            logger.info(f"优化后的结果: {result[:50]}...")
                        except Exception as e:
                            # 优化失败时保留原始结果
                            logger.error(f"结果优化失败: {str(e)}")
                
                # 根据开关决定是否将结果翻译回中文
                if enable_trans:
                    translated = translate_to_chinese(result)
                    logger.info(f"最终返回结果: {translated[:50]}...")
                    return translated
                else:
                    logger.info(f"不进行翻译，直接返回英文结果")
                    return result
            except Exception as e:
                error_msg = f"增强查询失败: {str(e)}"
                logger.error(error_msg)
                return error_msg
        
        with gr.Tab("原始查询"):
            input1 = gr.Textbox(label="输入问题（如：太阳的质量）")
            output1 = gr.Textbox(label="原始答案")
            btn1 = gr.Button("查询")
            btn1.click(fn=raw_query_with_translation, inputs=[input1, enable_translation], outputs=output1)
        
        with gr.Tab("增强查询"):
            input2 = gr.Textbox(label="输入复杂问题（如：比较GDP和人口增长的关系）")
            output2 = gr.Textbox(label="优化后的答案")
            btn2 = gr.Button("增强查询")
            btn2.click(fn=enhanced_query_with_translation, inputs=[input2, enable_translation], outputs=output2)
        
        # 示例区域
        with gr.Accordion("示例问题", open=True):
            gr.Examples(
                examples=[
                    ["地球到月球的距离"],
                    ["COVID-19的R0值"],
                    ["y = x^2 的导数"],
                    ["法国总统的年龄"]
                ],
                inputs=input1
            )
            gr.Examples(
                examples=[
                    ["distance between Earth and Moon"],
                    ["R0 value of COVID-19"],
                    ["derivative of y = x^2"],
                    ["age of French president"]
                ],
                inputs=input1,
                label="英文示例"
            )
    
    return demo

if __name__ == "__main__":
    # 启动Gradio界面
    logger.info("初始化Gradio界面")
    interface = create_interface()
    logger.info("启动Web服务")
    interface.launch(server_name="0.0.0.0", share=False)
    logger.info("Web服务已关闭")