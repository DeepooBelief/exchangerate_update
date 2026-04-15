import requests
from bs4 import BeautifulSoup
import sys

# ================= 配置区 =================
# 尝试从 GitHub Actions 动态生成的 info.py 中导入 Token 和 Topic
try:
    from info import PUSHPLUS_TOKEN, PUSHPLUS_TOPIC
except ImportError:
    print("❌ 错误: 未找到 info.py 文件或变量缺失。请检查 GitHub Actions 工作流。")
    PUSHPLUS_TOKEN = ""
    PUSHPLUS_TOPIC = ""
# ==========================================

def send_pushplus(title, content):
    """通过 PushPlus 发送微信通知（支持群组）"""
    if not PUSHPLUS_TOKEN:
        print("提示: PUSHPLUS_TOKEN 为空，跳过发送微信通知。")
        return
        
    url = 'http://www.pushplus.plus/send'
    
    # 构建发送数据
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }
    
    # 如果配置了群组编码，则加入 topic 参数进行群发
    if PUSHPLUS_TOPIC:
        data["topic"] = PUSHPLUS_TOPIC
        print(f"提示: 检测到群组编码 {PUSHPLUS_TOPIC}，准备发送群组消息...")
    else:
        print("提示: 未配置群组编码(Topic)，将默认发送一对一消息...")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get('code') == 200:
            print("✅ PushPlus 消息发送成功！请查收微信。")
        else:
            print(f"❌ PushPlus 消息发送失败: {result.get('msg')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ PushPlus 请求发生网络错误: {e}")

def get_gbp_rate():
    url = 'https://www.boc.cn/sourcedb/whpj/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8' 
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tr_list = soup.find_all('tr')
        
        for tr in tr_list:
            tds = tr.find_all('td')
            if len(tds) < 8:
                continue
            
            currency_name = tds[0].text.strip()
            
            if currency_name == '英镑':
                buying_rate = tds[1].text.strip()
                cash_buying_rate = tds[2].text.strip()
                selling_rate = tds[3].text.strip()
                cash_selling_rate = tds[4].text.strip()
                publish_date = tds[6].text.strip()
                publish_time = tds[7].text.strip()
                
                print(f"获取成功！更新时间: {publish_date} {publish_time}")
                print(f"现汇买入价: {buying_rate} | 现汇卖出价: {selling_rate}")
                
                title = f"{currency_name}现汇买入价: {buying_rate}"
                content = f"""
                <p><b>货币名称:</b> {currency_name}</p>
                <p><b>现汇买入价:</b> <span style="color:red">{buying_rate}</span></p>
                <p><b>现钞买入价:</b> {cash_buying_rate}</p>
                <p><b>现汇卖出价:</b> <span style="color:green">{selling_rate}</span></p>
                <p><b>现钞卖出价:</b> {cash_selling_rate}</p>
                <hr>
                <p><small>更新时间: {publish_date} {publish_time}</small></p>
                """
                
                send_pushplus(title, content)
                return

        print("网页解析成功，但未在表格中找到'英镑'的汇率信息。")

    except requests.exceptions.RequestException as e:
        print(f"爬虫网络请求失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"程序解析时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("正在获取中国银行英镑最新汇率...")
    get_gbp_rate()