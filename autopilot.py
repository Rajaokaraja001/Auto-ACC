#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOPILOT v4.0.0 - Multi-Account Forge
Shadow Hacker™ - Infinite scalability, zero friction.
"""

import asyncio
import os
import re
import sys
import random
import string
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
        self.temp_mail_url = os.getenv('TEMP_MAIL_URL', 'https://www.guerrillamail.com/')
        self.target_url = os.getenv('TARGET_URL', 'https://app.reve.com/')
        self.target_name = os.getenv('TARGET_NAME', 'reve')
        self.account_count = int(os.getenv('ACCOUNT_COUNT', '1'))  # Set this in workflow
        self.credentials = []
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def generate_username(self):
        """Generate a unique username for each account."""
        return f"Butter_{random.randint(10000, 99999)}"

    def generate_password(self, length=12):
        """Generate a strong password."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))

    async def harvest_temp_email(self, page):
        """Get a fresh temp email from GuerrillaMail."""
        await page.goto(self.temp_mail_url, wait_until='networkidle', timeout=60000)
        # Wait for email to appear
        for _ in range(10):
            email_element = await page.query_selector("#email")
            if email_element:
                email = await email_element.text_content()
                if email and '@' in email:
                    return email.strip()
            # Fallback regex
            content = await page.content()
            matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
            if matches:
                return matches[0]
            await asyncio.sleep(1)
        raise RuntimeError("Could not harvest temp email")

    async def run_account_creation(self, page, context, account_index):
        """Create one account and return credentials."""
        # 1. Get fresh temp email
        temp_email = await self.harvest_temp_email(page)
        username = self.generate_username()
        password = self.generate_password()
        logger.info(f"🆕 Account #{account_index}: {temp_email} | {username} | {password}")

        # 2. Navigate to target signup
        logger.info(f"🎯 Navigating to target: {self.target_url}")
        await page.goto(self.target_url, wait_until='networkidle', timeout=60000)
        await self._screenshot(page, f"target-{account_index}")

        # Click "Start Creating" CTA
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
                    logger.info("✅ CTA clicked.")
                    break
            except:
                continue
        await asyncio.sleep(2)

        # Fill form
        email_field = await self._find_and_fill(page, "email", temp_email)
        if email_field:
            await email_field.fill(temp_email)

        name_field = await self._find_and_fill(page, "name", username)
        if name_field:
            await name_field.fill(username)

        pass_field = await self._find_and_fill(page, "password", password)
        if pass_field:
            await pass_field.fill(password)

        # Submit
        submit_btn = await page.query_selector("button[type='submit'], button:has-text('Sign Up'), button:has-text('Create'), button:has-text('Continue')")
        if submit_btn and await submit_btn.is_visible():
            await submit_btn.click()
        else:
            if pass_field:
                await pass_field.press("Enter")
            elif email_field:
                await email_field.press("Enter")

        # 3. Poll for verification (now we need to check the same temp mail)
        logger.info(f"⏳ Waiting for verification for account {account_index}...")
        verification_found = False
        for attempt in range(20):
            await asyncio.sleep(5)
            await page.reload(wait_until='networkidle')
            content = await page.content()

            # Look for link or code
            links = re.findall(r'href="(https?://[^"]*)"', content)
            for link in links:
                if self.target_name.lower() in link.lower() or 'verify' in link.lower():
                    # We have a link – navigate to it
                    logger.info(f"🔗 Verification link found: {link[:100]}")
                    await page.goto(link, wait_until='networkidle')
                    verification_found = True
                    break
            if verification_found:
                break

            codes = re.findall(r'\b(\d{5,7})\b', content)
            for code in codes:
                if len(code) >= 5:
                    # Try to find a code input on the target page (maybe we're redirected)
                    code_input = await self._find_field(page, "code")
                    if code_input:
                        await code_input.fill(code)
                        confirm = await page.query_selector("button:has-text('Verify'), button:has-text('Confirm')")
                        if confirm:
                            await confirm.click()
                            verification_found = True
                            break
            if verification_found:
                break
        if not verification_found:
            logger.warning(f"⚠️ Account {account_index} verification not completed.")

        # Return credentials
        return {
            'email': temp_email,
            'username': username,
            'password': password,
            'verified': verification_found
        }

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

            # Loop for each account
            for i in range(1, self.account_count + 1):
                try:
                    creds = await self.run_account_creation(page, context, i)
                    self.credentials.append(creds)
                    # Save credentials to file after each success
                    with open(f"{self.screenshot_dir}/credentials.txt", "a") as f:
                        f.write(f"Account {i}: {creds['email']} | {creds['username']} | {creds['password']} | Verified: {creds['verified']}\n")
                except Exception as e:
                    logger.error(f"❌ Account {i} failed: {e}")
                    # Continue to next

            # Final screenshot and close
            await self._screenshot(page, "done")
            await browser.close()
            logger.info(f"🏁 Completed {len(self.credentials)} accounts.")

    # Helper methods (same as before)
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
            logger.info(f"📸 Screenshot: {filename}")
        except Exception as e:
            logger.warning(f"Could not screenshot {name}: {e}")

async def main():
    bot = CloudAutomator()
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
