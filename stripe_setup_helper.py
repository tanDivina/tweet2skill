#!/usr/bin/env python3
"""
stripe_setup_helper.py — Automatic Stripe product, pricing, webhook, and Vercel setup utility.

This utility streamlines Stripe configuration for Tweet2Skill:
  1. Verifies your Stripe Secret Key (sk_test_... or sk_live_...)
  2. Creates the "Tweet2Skill Pro" Product and $5/month recurring Price on Stripe (if they don't exist)
  3. Generates a Stripe Payment Link with standard prefill compatibility
  4. Configures the Stripe Webhook pointing to your production Vercel deployment URL
  5. Automatically pushes the generated keys directly to your Vercel Environment using Vercel CLI!
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import subprocess

# Ensure we print beautifully in neon colors
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title):
    print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")

def print_success(msg):
    print(f"{GREEN}✔ {msg}{RESET}")

def print_info(msg):
    print(f"{CYAN}ℹ {msg}{RESET}")

def print_warn(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✘ {msg}{RESET}")

def stripe_request(api_key, endpoint, data=None, method="POST"):
    """Makes a zero-dependency POST or GET request to the Stripe API."""
    url = f"https://api.stripe.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    req_data = None
    if data:
        # Stripe API expects application/x-www-form-urlencoded
        req_data = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method if data else "GET")
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            message = err_json.get("error", {}).get("message", err_msg)
        except Exception:
            message = err_msg
        print_error(f"Stripe API request failed: {message}")
        raise RuntimeError(message)

def get_vercel_project_url():
    """Tries to read the production domain from Vercel CLI."""
    try:
        res = subprocess.run(["npx", "vercel", "domains", "list"], capture_output=True, text=True, check=True)
        # Parse output for domain
        lines = res.stdout.strip().split("\n")
        for line in lines:
            if "hero-apps.com" in line:
                return "https://tweet2skill.hero-apps.com"
        print_warn("Could not find tweet2skill.hero-apps.com in vercel domain list. Defaulting...")
    except Exception:
        pass
    return "https://tweet2skill.hero-apps.com"

def main():
    print(f"{BOLD}{GREEN}⚡ Welcome to the Tweet2Skill Stripe Auto-Setup Wizard! ⚡{RESET}")
    print("This script will configure your Stripe products, payment links, webhooks, and push them to Vercel.\n")
    
    # Get Stripe API Key
    stripe_key = input(f"{BOLD}{YELLOW}Enter your Stripe Secret Key (starts with sk_test_ or sk_live_): {RESET}").strip()
    if not stripe_key:
        print_error("Stripe Secret Key is required. Exiting.")
        sys.exit(1)
        
    print_info("Verifying Stripe Secret Key...")
    try:
        account_info = stripe_request(stripe_key, "accounts", method="GET")
        account_id = account_info.get("data", [{}])[0].get("id", "unknown")
        print_success(f"Connected to Stripe Account ID: {account_id}")
    except Exception as e:
        print_error(f"Invalid Stripe Secret Key: {e}")
        sys.exit(1)

    # 1. Check or Create Product
    print_header("1. Configuring Stripe Product")
    product_id = None
    try:
        # Search for existing Tweet2Skill product
        existing_products = stripe_request(stripe_key, "products", method="GET")
        for prod in existing_products.get("data", []):
            if prod.get("name") == "Tweet2Skill Pro":
                product_id = prod.get("id")
                print_success(f"Found existing product: {prod.get('name')} (ID: {product_id})")
                break
        
        if not product_id:
            print_info("Product 'Tweet2Skill Pro' not found. Creating a new one...")
            prod_data = {
                "name": "Tweet2Skill Pro",
                "description": "Premium access to thread extraction, pro deep capture, and infinite AI agent skills.",
                "metadata[app]": "tweet2skill"
            }
            new_prod = stripe_request(stripe_key, "products", data=prod_data)
            product_id = new_prod.get("id")
            print_success(f"Created Product: Tweet2Skill Pro (ID: {product_id})")
    except Exception as e:
        print_error(f"Failed to configure Stripe Product: {e}")
        sys.exit(1)

    # 2. Check or Create Price
    print_header("2. Configuring Recurring Pricing ($5/month)")
    price_id = None
    try:
        existing_prices = stripe_request(stripe_key, f"prices?product={product_id}", method="GET")
        for pr in existing_prices.get("data", []):
            if pr.get("recurring", {}).get("interval") == "month" and pr.get("unit_amount") == 500:
                price_id = pr.get("id")
                print_success(f"Found matching monthly price: $5.00 (ID: {price_id})")
                break
                
        if not price_id:
            print_info("Recurring Price not found. Creating a $5/month Price...")
            price_data = {
                "product": product_id,
                "unit_amount": "500",
                "currency": "usd",
                "recurring[interval]": "month",
                "metadata[app]": "tweet2skill"
            }
            new_price = stripe_request(stripe_key, "prices", data=price_data)
            price_id = new_price.get("id")
            print_success(f"Created monthly recurring Price: $5.00 USD (ID: {price_id})")
    except Exception as e:
        print_error(f"Failed to configure Price: {e}")
        sys.exit(1)

    # 3. Create Stripe Payment Link
    print_header("3. Creating Stripe Payment Link")
    payment_link_url = None
    try:
        # Check if we already have payment links
        existing_links = stripe_request(stripe_key, "payment_links", method="GET")
        for link in existing_links.get("data", []):
            line_items = link.get("line_items", {}).get("data", [])
            if line_items and line_items[0].get("price") == price_id:
                payment_link_url = link.get("url")
                print_success(f"Found existing Stripe Payment Link: {payment_link_url}")
                break
                
        if not payment_link_url:
            print_info("Creating standard Stripe Payment Link...")
            link_data = {
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": "1",
                "metadata[app]": "tweet2skill",
                "allow_promotion_codes": "true",
            }
            new_link = stripe_request(stripe_key, "payment_links", data=link_data)
            payment_link_url = new_link.get("url")
            print_success(f"Created Stripe Payment Link: {payment_link_url}")
    except Exception as e:
        print_error(f"Failed to configure Payment Link: {e}")
        sys.exit(1)

    # 4. Configure Webhook
    print_header("4. Setting Up Vercel Webhook on Stripe")
    webhook_secret = None
    target_url = get_vercel_project_url() + "/api/webhook"
    print_info(f"Target URL for Stripe Webhooks: {target_url}")
    
    try:
        # Search for existing webhook pointing to target_url
        existing_endpoints = stripe_request(stripe_key, "webhook_endpoints", method="GET")
        for ep in existing_endpoints.get("data", []):
            if ep.get("url") == target_url:
                print_success(f"Webhook already registered on Stripe (ID: {ep.get('id')})")
                print_warn("Stripe does not expose your webhook signing secret after creation for security reasons.")
                recreate = input(f"{BOLD}{YELLOW}Do you want to re-create the webhook endpoint to get a fresh signing secret? (y/n): {RESET}").strip().lower()
                if recreate == 'y':
                    # Delete the old one
                    print_info(f"Deleting old webhook endpoint {ep.get('id')}...")
                    stripe_request(stripe_key, f"webhook_endpoints/{ep.get('id')}", method="DELETE")
                else:
                    webhook_secret = input(f"{BOLD}{YELLOW}Please enter your existing STRIPE_WEBHOOK_SECRET (whsec_...): {RESET}").strip()
                break

        if not webhook_secret:
            print_info("Registering fresh Webhook endpoint on Stripe...")
            webhook_data = {
                "url": target_url,
                "enabled_events[0]": "checkout.session.completed",
                "enabled_events[1]": "customer.subscription.updated",
                "enabled_events[2]": "customer.subscription.deleted",
                "description": "Tweet2Skill subscription webhook receiver"
            }
            new_ep = stripe_request(stripe_key, "webhook_endpoints", data=webhook_data)
            webhook_secret = new_ep.get("secret")
            print_success("Successfully registered Webhook endpoint!")
            print(f"{BOLD}{GREEN}Your Webhook Signing Secret: {webhook_secret}{RESET}")
    except Exception as e:
        print_error(f"Failed to configure Webhook Endpoint: {e}")
        sys.exit(1)

    # 5. Push Environment Variables to Vercel
    print_header("5. Pushing Credentials to Vercel")
    print_info("Piping environment configurations to Vercel production server...")
    
    try:
        # Set STRIPE_WEBHOOK_SECRET
        print_info("Adding STRIPE_WEBHOOK_SECRET to Vercel...")
        subprocess.run(["npx", "vercel", "env", "rm", "STRIPE_WEBHOOK_SECRET", "production", "-y"], capture_output=True)
        env_secret_proc = subprocess.Popen(["npx", "vercel", "env", "add", "STRIPE_WEBHOOK_SECRET", "production"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        env_secret_proc.communicate(input=webhook_secret)
        
        # Set STRIPE_API_KEY
        print_info("Adding STRIPE_API_KEY to Vercel...")
        subprocess.run(["npx", "vercel", "env", "rm", "STRIPE_API_KEY", "production", "-y"], capture_output=True)
        env_key_proc = subprocess.Popen(["npx", "vercel", "env", "add", "STRIPE_API_KEY", "production"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        env_key_proc.communicate(input=stripe_key)

        print_success("Configured both STRIPE_WEBHOOK_SECRET and STRIPE_API_KEY on Vercel!")
        
        # Deploy Vercel with fresh env variables
        print_info("Re-deploying Vercel project in production to apply changes...")
        subprocess.run(["npx", "vercel", "--prod", "--yes"], check=True)
        print_success("Vercel project re-deployed successfully and is live with Stripe!")
        
    except Exception as e:
        print_error(f"Failed to complete Vercel configuration automatically: {e}")
        print_warn("Please manually add these variables in your Vercel Dashboard:")
        print(f"  - STRIPE_WEBHOOK_SECRET = {webhook_secret}")
        print(f"  - STRIPE_API_KEY = {stripe_key}")
        sys.exit(1)

    print(f"\n{BOLD}{GREEN}🎉 STRIPE CONFIGURATION IS 100% COMPLETE! 🎉{RESET}")
    print(f"Your monthly subscription Stripe Checkout link is:")
    print(f"👉 {BOLD}{CYAN}{payment_link_url}{RESET}\n")
    print("If you need to update popup.js, verify that 'stripeCheckoutUrl' in chrome.storage.local")
    print("is updated, or set it statically in the config.")

if __name__ == "__main__":
    main()
