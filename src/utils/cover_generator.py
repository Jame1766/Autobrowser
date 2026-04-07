from playwright.sync_api import sync_playwright
import time
import os


def generate_cover(text, output_path="cover.png", timeout_ms=30000):
    """使用 MD2Card 生成小红书封面图片"""
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)

    # 清理文本
    text = text.strip()[:20]  # 限制长度
    if not text:
        text = "AI资讯"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 设置下载行为
        context = browser.new_context()
        page = context.new_page()

        try:
            print("[1/5] 打开网页...")
            page.goto("https://md2card.cn/zh/cover", timeout=60000)
            page.wait_for_timeout(2000)  # 减少等待时间

            print("[2/5] 输入文字...")
            textarea_xpath = "xpath=/html/body/main/div/div/div/div[2]/div/div[1]/textarea"
            page.locator(textarea_xpath).fill(text)
            page.wait_for_timeout(300)

            print("[3/5] 点击生成按钮...")
            button_xpath = "xpath=/html/body/main/div/div/div/div[2]/div/div[2]/div[2]/button[2]"
            page.locator(button_xpath).click()

            print("[4/5] 等待生成图片...")
            page.wait_for_timeout(3000)  # 减少等待时间

            print("[5/5] 点击下载按钮...")
            # 等待下载按钮出现
            try:
                page.wait_for_selector("button:has-text('下载')", timeout=timeout_ms)
            except:
                # 如果找不到下载按钮，尝试截图保存
                print("下载按钮未找到，尝试截图...")
                page.screenshot(path=output_path, full_page=False)
                print(f"完成! 封面已截图保存到: {output_path}")
                return output_path

            # 监听下载事件
            with page.expect_download() as download_info:
                page.locator("button:has-text('下载')").first.click()

            download = download_info.value
            # 保存文件
            download.save_as(output_path)

            print(f"完成! 封面已保存到: {output_path}")
            return output_path

        except Exception as e:
            print(f"错误: {e}")
            try:
                page.screenshot(path="error.png")
            except:
                pass
            return None

        finally:
            browser.close()


if __name__ == "__main__":
    text = """分享一个免费的小红书封面工具
MD2Card"""

    generate_cover(text, "my_cover.png")
