#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOPILOT v3.9.0 - Cloud Edition (Fixed Temp-Mail)
Shadow Hacker™ - Adaptive, resilient, unstoppable.
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ShadowBot")

class CloudAutomator:
    def __init__(self):
        # Use GuerrillaMail - much more stable
        self.temp_mail_url = os.getenv('TEMP_MAIL_URL', 'https://www.guerrillamail.com/')
        self.target_url = os.getenv('TARGET_URL', 'https://app.reve.com/')
        self.target_name = os.getenv('TARGET_NAME', 'reve')
        self.temp_email = None
        self.verification_code = None
        self.verification_link = None
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1280,720'
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            """)

            page = await context.new_page()
            await self._screenshot(page, "start")

            # --- 1. HARVEST TEMP EMAIL (GuerrillaMail specific) ---
            logger.info(f"🌐 Opening temp-mail: {self.temp_mail_url}")
            await page.goto(self.temp_mail_url, wait_until='networkidle', timeout=60000)
            await self._screenshot(page, "temp-mail-loaded")

            # Strategy 1: Look for the email address in visible text (GuerrillaMail shows it in a span)
            email_element = await page.query_selector("#email")
            if email_element:
                self.temp_email = await email_element.text_content()
                self.temp_email = self.temp_email.strip()
            if not self.temp_email:
                # Strategy 2: Scan all text for email pattern
                content = await page.content()
                matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                if matches:
                    self.temp_email = matches[0]
            if not self.temp_email:
                # Strategy 3: click the copy button (if exists) and read from input
                copy_btn = await page.query_selector("button:has-text('copy'), button:has-text('Copy'), [aria-label*='copy']")
                if copy_btn:
                    await copy_btn.click()
                    await asyncio.sleep(0.5)
                    email_input = await page.query_selector("input[type='text'], input[type='email']")
                    if email_input:
                        self.temp_email = await email_input.input_value()
            if not self.temp_email:
                # Strategy 4: get from the iframe or any element with id 'email'
                email_input = await page.query_selector("input#email")
                if email_input:
                    self.temp_email = await email_input.input_value()
            if not self.temp_email:
                raise RuntimeError("Failed to harvest temp email – check site structure.")
            logger.info(f"📧 Captured: {self.temp_email}")

            # --- 2. TARGET SIGNUP (same as before) ---
            # ... (rest of the code unchanged; I'll include it below for completeness)

            # [The rest of the script remains identical to the previous version,
            #  but for brevity I'll include it fully here – you can just keep your old script
            #  and only replace the email harvesting part. But I'll give the whole thing
            #  to avoid any confusion.]

            logger.info(f"🎯 Navigating to target: {self.target_url}")
            await page.goto(self.target_url, wait_until='networkidle', timeout=60000)
            await self._screenshot(page, "target-loaded")

            cta_found = False
            for sel in [
                "button:has-text('Start Creating')",
                "button:has-text('Start')",
                "button:has-text('Create Account')",
                "button:has-text('Sign Up')",
                "a:has-text('Start Creating')"
            ]:
                try:
                    btn = await page.wait_for_selector(sel, timeout=3000)
                    if btn and await btn.is_visible():
                        await btn.click()
                        cta_found = True
                        logger.info("✅ Primary CTA clicked.")
                        await self._screenshot(page, "cta-clicked")
                        break
                except:
                    continue
            if not cta_found:
                logger.warning("⚠️ No explicit CTA – may be direct form.")

            await asyncio.sleep(2)
            await self._screenshot(page, "before-fill")

            email_field = await self._find_and_fill(page, "email", self.temp_email)
            if email_field:
                await email_field.fill(self.temp_email)

            name_field = await self._find_and_fill(page, "name", "Butter Cloud")
            if name_field:
                await name_field.fill("Butter Cloud")

            pass_field = await self._find_and_fill(page, "password", "ShadowCloud#2026!")
            if pass_field:
                await pass_field.fill("ShadowCloud#2026!")

            submit_btn = await page.query_selector("button[type='submit'], button:has-text('Sign Up'), button:has-text('Create'), button:has-text('Continue')")
            if submit_btn and await submit_btn.is_visible():
                await submit_btn.click()
                logger.info("🚀 Form submitted.")
            else:
                if pass_field:
                    await pass_field.press("Enter")
                elif email_field:
                    await email_field.press("Enter")

            await self._screenshot(page, "after-submit")

            # --- 3. POLL TEMP-MAIL FOR VERIFICATION ---
            logger.info("⏳ Polling for verification email...")
            verification_found = False
            for attempt in range(25):
                await asyncio.sleep(6)
                await page.reload(wait_until='networkidle')
                content = await page.content()

                links = re.findall(r'href="(https?://[^"]*)"', content)
                for link in links:
                    if self.target_name.lower() in link.lower() or 'verify' in link.lower() or 'confirm' in link.lower():
                        self.verification_link = link
                        verification_found = True
                        logger.info(f"🔗 Verification link: {link[:100]}...")
                        break
                if verification_found:
                    break

                codes = re.findall(r'\b(\d{5,7})\b', content)
                for code in codes:
                    if len(code) >= 5:
                        self.verification_code = code
                        verification_found = True
                        logger.info(f"🔢 Verification code: {code}")
                        break
                if verification_found:
                    break

                code_ctx = re.findall(r'code[:\s]+(\d{4,8})', content, re.IGNORECASE)
                if code_ctx:
                    self.verification_code = code_ctx[0]
                    verification_found = True
                    break

                logger.info(f"⏳ Poll {attempt+1}/25 – waiting...")
                await self._screenshot(page, f"poll-{attempt}")

            if not verification_found:
                logger.warning("⚠️ No verification found – saving final state.")
                await self._screenshot(page, "final-state")
                with open("final_page.html", "w", encoding="utf-8") as f:
                    f.write(await page.content())

            if self.verification_link:
                logger.info("🌐 Navigating to verification link...")
                await page.goto(self.verification_link, wait_until='networkidle', timeout=60000)
                await self._screenshot(page, "verified")
                logger.info("✅ Verification completed successfully.")
            elif self.verification_code:
                code_input = await self._find_field(page, "code")
                if code_input:
                    await code_input.fill(self.verification_code)
                    confirm = await page.query_selector("button:has-text('Verify'), button:has-text('Confirm')")
                    if confirm:
                        await confirm.click()
                        await self._screenshot(page, "code-submitted")
                        logger.info("✅ Code submitted.")
            else:
                logger.info("ℹ️ No explicit verification step – account may already be active.")

            logger.info("🏁 Automation finished. Saving artifacts.")
            await self._screenshot(page, "done")
            await browser.close()

    async def _find_and_fill(self, page, field_type, value):
        base = f"input[type='{field_type}'], input[name*='{field_type}'], input[id*='{field_type}'], input[placeholder*='{field_type}']"
        try:
            el = await page.wait_for_selector(base, timeout=4000)
            if el and await el.is_visible():
                await el.fill(value)
                return el
        except:
            pass
        all_inputs = await page.query_selector_all("input:visible")
        for inp in all_inputs:
            attrs = {
                'placeholder': await inp.get_attribute('placeholder') or '',
                'aria-label': await inp.get_attribute('aria-label') or '',
                'name': await inp.get_attribute('name') or '',
                'id': await inp.get_attribute('id') or ''
            }
            combined = ' '.join(attrs.values()).lower()
            if field_type in combined:
                await inp.fill(value)
                return inp
        return None

    async def _find_field(self, page, field_type):
        base = f"input[type='{field_type}'], input[name*='{field_type}'], input[id*='{field_type}'], input[placeholder*='{field_type}']"
        try:
            el = await page.wait_for_selector(base, timeout=2000)
            return el
        except:
            return None

    async def _screenshot(self, page, name):
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{self.screenshot_dir}/{name}_{timestamp}.png"
            await page.screenshot(path=filename, full_page=True)
            logger.info(f"📸 Screenshot saved: {filename}")
        except Exception as e:
            logger.warning(f"Could not screenshot {name}: {e}")

async def main():
    bot = CloudAutomator()
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
