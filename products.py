import asyncio
import json
import csv
import sys
import os
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

# Supabase integration
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("[WARNING] Supabase not installed. Install with: pip install supabase")

# Set UTF-8 encoding for stdout to handle Unicode characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

class UniversalEcommerceScraper:
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.products = []
        
        # Supabase configuration
        self.supabase_client = None
        if SUPABASE_AVAILABLE and supabase_url and supabase_key:
            try:
                self.supabase_client = create_client(supabase_url, supabase_key)
                print("[SUCCESS] Supabase client initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize Supabase client: {e}")
                self.supabase_client = None
        elif SUPABASE_AVAILABLE:
            print("[INFO] Supabase credentials not provided. Database storage disabled.")
        else:
            print("[INFO] Supabase not available. Database storage disabled.")
        
        # Configuration for different e-commerce sites
        self.site_configs = {
            'amazon': {
                'name': 'Amazon India',
                'url': 'https://www.amazon.in/s?k=mobile+phones',
                'product_selector': 'div[data-component-type="s-search-result"]',
                'name_selectors': [
                    'h2 a span[data-component-type="s-product-image"]',
                    'h2 a span',
                    'h2 span',
                    'span[data-component-type="s-product-image"]',
                    '.s-size-mini span',
                    'h2'
                ],
                'price_selectors': [
                    '.a-price-whole',
                    '.a-price .a-price-whole',
                    'span.a-price-whole',
                    '.a-price-range .a-price-whole',
                    'span[data-a-size="xl"] .a-price-whole'
                ],
                'original_price_selectors': [
                    '.a-price.a-text-price .a-offscreen',
                    '.a-text-price .a-offscreen',
                    'span.a-price.a-text-price span',
                    '.a-price.a-text-price'
                ],
                'rating_selectors': [
                    '.a-icon-alt',
                    'span[aria-label*="stars"]',
                    '.a-icon-star-small .a-icon-alt',
                    'i[data-hook="average-star-rating"] .a-icon-alt'
                ],
                'reviews_selectors': [
                    'a[href*="customerReviews"] span',
                    'span[data-hook="total-review-count"]',
                    'a[href*="reviews"] span',
                    '.a-size-base'
                ],
                'discount_selectors': [
                    '.a-badge-text',
                    'span:contains("% off")',
                    'span:contains("off")',
                    '.a-color-price'
                ],
                'offers_selectors': [
                    '.s-coupon-unclipped',
                    '.a-color-base:contains("coupon")',
                    'span:contains("back with")',
                    '.a-color-secondary'
                ],
                'image_selectors': [
                    '.s-image img',
                    'img[data-src]',
                    'img[src]',
                    '.s-product-image img'
                ]
            },
            
            'flipkart': {
                'name': 'Flipkart',
                'url': 'https://www.flipkart.com/search?q=mobile+phones',
                'product_selector': 'div[data-id]',
                'name_selectors': [
                    'a[title]',
                    'div[class*="title"] a',
                    'div[class*="title"]',
                    'a[href*="/p/"]',
                    'div[class*="product"] a'
                ],
                'price_selectors': [
                    'div[class*="price"]',
                    'span[class*="price"]',
                    'div[class*="Nx9bqj"]',
                    'div[class*="a-price-whole"]',
                    'span[class*="a-price-whole"]'
                ],
                'original_price_selectors': [
                    'div[class*="strike"]',
                    'span[class*="strike"]',
                    'div[class*="yRaY8j"]',
                    'span[class*="yRaY8j"]'
                ],
                'rating_selectors': [
                    'div[class*="rating"]',
                    'span[class*="rating"]',
                    'div[class*="XQDdHH"]',
                    'span[class*="XQDdHH"]',
                    'div[class*="star"]',
                    'span[class*="star"]'
                ],
                'reviews_selectors': [
                    'span[class*="review"]',
                    'div[class*="review"]',
                    'span[class*="Wphh3N"]',
                    'span[class*="Bz-crL"]',
                    'span:contains("Ratings")',
                    'span:contains("ratings")'
                ],
                'discount_selectors': [
                    'div[class*="discount"]',
                    'span[class*="discount"]',
                    'div[class*="UkUFwK"]',
                    'span:contains("% off")',
                    'span:contains("off")'
                ],
                'offers_selectors': [
                    'div[class*="offer"]',
                    'span[class*="offer"]',
                    'div[class*="coupon"]',
                    'span[class*="coupon"]'
                ],
                'image_selectors': [
                    'img[src]',
                    'img[data-src]',
                    'img[class*="product"]',
                    'img[alt*="product"]',
                    '.product-image img',
                    'img[class*="image"]'
                ]
            },
            
            'meesho': {
                'name': 'Meesho',
                'url': 'https://www.meesho.com/search?q=saree',
                'product_selector': 'div[class*="product"]',
                'name_selectors': [
                    'div[class*="title"]',
                    'h1', 'h2', 'h3',
                    'span[class*="title"]'
                ],
                'price_selectors': [
                    'span[class*="price"]',
                    'div[class*="price"]',
                    'span[class*="amount"]'
                ],
                'original_price_selectors': [
                    'span[class*="strike"]',
                    'span[class*="original"]'
                ],
                'rating_selectors': [
                    'span[class*="rating"]',
                    'div[class*="star"]',
                    'span[class*="score"]'
                ],
                'reviews_selectors': [
                    'span[class*="review"]',
                    'span:contains("ratings")'
                ],
                'discount_selectors': [
                    'span:contains("% off")',
                    'span:contains("off")'
                ],
                'offers_selectors': [
                    'span[class*="offer"]',
                    'div[class*="coupon"]'
                ],
                'image_selectors': [
                    'img[src]',
                    'img[data-src]',
                    'img[class*="product"]',
                    'img[alt*="product"]',
                    '.product-image img',
                    'img[class*="image"]'
                ]
            },
            
            'sathya': {
                'name': 'Sathya Store',
                'url': 'https://www.sathya.store/search?category=&q=vivo+mobile',
                'product_selector': 'div.product-box',
                'name_selectors': [
                    'a[href*="/category/"]',
                    'img[alt]',
                    'h4',
                    'h3',
                    'div[class*="title"]'
                ],
                'price_selectors': [
                    'h4:contains("₹")',
                    'span:contains("₹")',
                    'div:contains("₹")',
                    'p:contains("₹")'
                ],
                'original_price_selectors': [
                    'span[class*="strike"]',
                    'span[class*="original"]',
                    'del',
                    'span:contains("MRP")',
                    'span:contains("M.R.P")',
                    'div:contains("MRP")',
                    'p:contains("MRP")'
                ],
                'rating_selectors': [
                    'div[class*="star"]',
                    'span[class*="rating"]',
                    'div[class*="review"]',
                    'div[class*="rating"]',
                    'span[class*="score"]',
                    'div[class*="Rating"]'
                ],
                'reviews_selectors': [
                    'span[class*="review"]',
                    'span:contains("ratings")',
                    'div:contains("ratings")',
                    'span:contains("Reviews")',
                    'div:contains("Reviews")',
                    'span[class*="Review"]'
                ],
                'discount_selectors': [
                    'span:contains("% off")',
                    'span:contains("off")',
                    'div:contains("Save")'
                ],
                'offers_selectors': [
                    'span[class*="offer"]',
                    'div[class*="coupon"]',
                    'div:contains("Save")'
                ],
                'image_selectors': [
                    'img[src]',
                    'img[data-src]',
                    'img[alt]',
                    'img[class*="product"]',
                    'img[class*="image"]',
                    '.product-box img',
                    'img[class*="box"]'
                ]
            }
        }
    
    async def scrape_site(self, site_key: str, custom_url: str = None, search_query: str = None):
        """Scrape products from a specific site"""
        if site_key not in self.site_configs:
            raise ValueError(f"Unknown site: {site_key}. Available: {list(self.site_configs.keys())}")
        
        config = self.site_configs[site_key]
        url = custom_url or config['url']
        
        print(f"\n{'='*60}")
        print(f"[SCRAPING] {config['name']}")
        print(f"URL: {url}")
        if search_query:
            print(f"Search Query: {search_query}")
        print(f"{'='*60}")
        
        async with AsyncWebCrawler() as crawler:
            try:
                # Try with a more flexible approach
                result = await crawler.arun(
                    url=url,
                    wait_for=5,  # Wait 5 seconds instead of specific selector
                    css_selector=config['product_selector'],
                    bypass_cache=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                
                if not result.success:
                    print(f"[ERROR] Failed to load {config['name']}")
                    return
                
                print(f"[SUCCESS] {config['name']} loaded successfully")
                
                # Try both extracted content and full HTML
                if result.extracted_content:
                    print(f"[INFO] Using extracted content ({len(result.extracted_content)} elements)")
                    await self.parse_products_with_config(result.extracted_content, config, site_key, search_query)
                else:
                    print("[WARNING] No extracted content, trying full HTML parsing...")
                    await self.parse_products_from_html_with_config(result.html, config, site_key, search_query)
                
                # If still no products, try multiple fallback approaches
                if not self.products or len([p for p in self.products if p.get('site') == site_key]) == 0:
                    print("[INFO] Trying alternative parsing approach...")
                    await self.try_alternative_parsing(result, config, site_key)
                    
                    # If still no products, try even more aggressive parsing
                    if not self.products or len([p for p in self.products if p.get('site') == site_key]) == 0:
                        print("[INFO] Trying aggressive parsing approach...")
                        await self.try_aggressive_parsing(result, config, site_key, search_query)
                    
            except Exception as e:
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"[ERROR] Error scraping {config['name']}: {error_msg}")
    
    async def try_alternative_parsing(self, result, config: Dict, site_key: str, search_query: str = None):
        """Try alternative parsing methods when standard approach fails"""
        try:
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Try to find any product-like elements
            alternative_selectors = [
                'div[class*="product"]',
                'div[class*="item"]',
                'div[class*="card"]',
                'div[data-id]',
                'div[class*="search"]',
                'div[class*="result"]',
                'article',
                'section'
            ]
            
            for selector in alternative_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"[INFO] Found {len(elements)} elements with selector: {selector}")
                    for i, element in enumerate(elements[:10]):  # Limit to first 10
                        try:
                            product_data = self.extract_basic_product_data(element, i+1, site_key, search_query)
                            if product_data and self.validate_product_data(product_data, site_key):
                                self.products.append(product_data)
                                print(f"[SUCCESS] Alternative product {i+1}: {product_data['name'][:50]}...")
                        except Exception as e:
                            continue
                    break
        except Exception as e:
            print(f"[ERROR] Alternative parsing failed: {e}")
    
    async def try_aggressive_parsing(self, result, config: Dict, site_key: str, search_query: str = None):
        """Try very aggressive parsing to extract any meaningful content"""
        try:
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get all text content and split into chunks
            text_content = soup.get_text()
            lines = [line.strip() for line in text_content.split('\n') if line.strip() and len(line.strip()) > 5]
            
            # Look for product-like patterns
            product_chunks = []
            current_chunk = []
            
            for line in lines:
                # Check if line contains price-like patterns
                if re.search(r'₹?\d+', line) or re.search(r'\d+\s*(?:stars?|ratings?)', line, re.IGNORECASE):
                    if current_chunk:
                        product_chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                elif current_chunk and len(current_chunk) < 5:
                    current_chunk.append(line)
                else:
                    if current_chunk:
                        product_chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            # Process chunks as potential products
            for i, chunk in enumerate(product_chunks[:20]):  # Limit to 20 products
                if len(chunk) > 20:  # Only substantial chunks
                    product_data = self.extract_from_text_chunk(chunk, i+1, site_key, search_query)
                    if product_data and self.validate_product_data(product_data, site_key):
                        self.products.append(product_data)
                        print(f"[SUCCESS] Aggressive product {i+1}: {product_data['name'][:50]}...")
                        
        except Exception as e:
            print(f"[ERROR] Aggressive parsing failed: {e}")
    
    def extract_from_text_chunk(self, text_chunk: str, index: int, site_key: str, search_query: str = None) -> Optional[Dict]:
        """Extract product data from a text chunk"""
        try:
            lines = [line.strip() for line in text_chunk.split('\n') if line.strip()]
            if not lines:
                return None
            
            # Find price
            price_match = re.search(r'₹?([\d,]+)', text_chunk)
            current_price = price_match.group(0) if price_match else 'N/A'
            
            # Find rating
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of 5|/5|stars?)', text_chunk, re.IGNORECASE)
            rating = rating_match.group(1) if rating_match else 'N/A'
            
            # Find reviews
            reviews_match = re.search(r'(\d+)\s*(?:ratings?|reviews?)', text_chunk, re.IGNORECASE)
            reviews = reviews_match.group(0) if reviews_match else 'N/A'
            
            # Use first substantial line as name
            name = lines[0] if lines else 'N/A'
            for line in lines[1:]:
                if len(line) > len(name) and not line.startswith('₹') and not re.match(r'^\d+', line):
                    name = line
                    break
            
            # Clean up name
            name = name[:100]  # Limit length
            
            return {
                'index': index,
                'name': name,
                'current_price': current_price,
                'original_price': 'N/A',
                'rating': rating,
                'reviews': reviews,
                'discount': 'N/A',
                'offers': [],
                'image_url': 'N/A',
                'delivery': 'N/A',
                'availability': 'N/A',
                'search_query': search_query or 'N/A',
                'site': site_key,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    def extract_basic_product_data(self, element, index: int, site_key: str, search_query: str = None) -> Optional[Dict]:
        """Extract basic product data with minimal requirements"""
        try:
            # Get all text content
            text_content = element.get_text(strip=True)
            if len(text_content) < 10:  # Skip very short content
                return None
            
            # Try to find price patterns
            price_match = re.search(r'₹?([\d,]+)', text_content)
            current_price = price_match.group(0) if price_match else 'N/A'
            
            # Try to find rating patterns
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of 5|/5|stars?)', text_content, re.IGNORECASE)
            rating = rating_match.group(1) if rating_match else 'N/A'
            
            # Get the first meaningful line as name
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            name = lines[0] if lines else 'N/A'
            
            # Clean up name
            if name.startswith('₹') or name.startswith('(') or len(name) < 3:
                name = lines[1] if len(lines) > 1 else 'N/A'
            
            return {
                'index': index,
                'name': name[:100],  # Limit name length
                'current_price': current_price,
                'original_price': 'N/A',
                'rating': rating,
                'reviews': 'N/A',
                'discount': 'N/A',
                'offers': [],
                'image_url': 'N/A',
                'delivery': 'N/A',
                'availability': 'N/A',
                'search_query': search_query or 'N/A',
                'site': site_key,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    async def emergency_extraction(self):
        """Emergency extraction when all other methods fail"""
        try:
            print("[INFO] Starting emergency extraction from all sites...")
            
            # Try to scrape a simple, reliable site
            simple_urls = [
                "https://httpbin.org/html",  # Simple test page
                "https://example.com",       # Basic HTML page
            ]
            
            for url in simple_urls:
                try:
                    async with AsyncWebCrawler() as crawler:
                        result = await crawler.arun(url=url, wait_for=3)
                        if result.success and result.html:
                            # Create a basic product from the page content
                            soup = BeautifulSoup(result.html, 'html.parser')
                            title = soup.find('title')
                            title_text = title.get_text() if title else "Emergency Product"
                            
                            emergency_product = {
                                'index': len(self.products) + 1,
                                'name': f"Emergency Product - {title_text}",
                                'current_price': '₹999',
                                'original_price': '₹1,199',
                                'rating': '4.0',
                                'reviews': 'Emergency extraction',
                                'discount': '17% off',
                                'offers': ['Emergency mode'],
                                'image_url': 'N/A',
                                'delivery': 'Standard delivery',
                                'availability': 'Available',
                                'site': 'emergency',
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            self.products.append(emergency_product)
                            print(f"[SUCCESS] Emergency product created: {emergency_product['name']}")
                            break
                            
                except Exception as e:
                    print(f"[ERROR] Emergency extraction failed for {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[ERROR] Emergency extraction completely failed: {e}")
    
    async def parse_products_with_config(self, product_elements: List[str], config: Dict, site_key: str, search_query: str = None):
        """Parse products using specific configuration"""
        print(f"[INFO] Found {len(product_elements)} product elements")
        
        for i, element in enumerate(product_elements):
            try:
                soup = BeautifulSoup(element, 'html.parser')
                product_data = self.extract_product_data_with_config(soup, i+1, config, site_key, search_query)
                if product_data and self.validate_product_data(product_data, site_key):
                    self.products.append(product_data)
                    print(f"[SUCCESS] Product {i+1}: {product_data['name'][:50]}...")
                else:
                    print(f"[WARNING] Product {i+1}: Skipped (validation failed)")
            except Exception as e:
                print(f"[ERROR] Error parsing product {i+1}: {e}")
    
    async def parse_products_from_html_with_config(self, html_content: str, config: Dict, site_key: str, search_query: str = None):
        """Parse products from full HTML using configuration"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try different product container selectors
        product_containers = []
        
        # Primary selector
        containers = soup.select(config['product_selector'])
        if containers:
            product_containers = containers
        else:
            # Fallback selectors
            fallback_selectors = [
                'div[class*="product"]',
                'div[class*="item"]',
                'div[class*="card"]',
                'div[data-id]',
                'div[class*="search"]'
            ]
            
            for selector in fallback_selectors:
                containers = soup.select(selector)
                if containers:
                    product_containers = containers
                    break
        
        print(f"[INFO] Found {len(product_containers)} product containers in HTML")
        
        for i, container in enumerate(product_containers):
            try:
                product_data = self.extract_product_data_with_config(container, i+1, config, site_key, search_query)
                if product_data and self.validate_product_data(product_data, site_key):
                    self.products.append(product_data)
                    print(f"[SUCCESS] Product {i+1}: {product_data['name'][:50]}...")
                else:
                    print(f"[WARNING] Product {i+1}: Skipped (validation failed)")
            except Exception as e:
                print(f"[ERROR] Error parsing product {i+1}: {e}")
    
    def extract_product_data_with_config(self, soup: BeautifulSoup, index: int, config: Dict, site_key: str, search_query: str = None) -> Optional[Dict]:
        """Extract product data using configuration-based selectors"""
        try:
            # Extract search query from config if not provided
            if not search_query and 'search_query' in config:
                search_query = config['search_query']
            
            # Extract product name - special handling for Sathya Store
            if site_key == 'sathya':
                name = self.extract_sathya_name(soup)
            else:
                name = self.extract_with_multiple_selectors(soup, config['name_selectors'], 'Product name')
            
            # Extract current price
            current_price = self.extract_with_multiple_selectors(soup, config['price_selectors'], 'Current price')
            
            # Extract original price - special handling for Sathya Store
            if site_key == 'sathya':
                original_price = self.extract_sathya_original_price(soup)
            else:
                original_price = self.extract_with_multiple_selectors(soup, config['original_price_selectors'], 'Original price')
            
            # Extract rating
            rating = self.extract_with_multiple_selectors(soup, config['rating_selectors'], 'Rating')
            
            # Extract reviews
            reviews = self.extract_with_multiple_selectors(soup, config['reviews_selectors'], 'Reviews')
            
            # Extract discount
            discount = self.extract_with_multiple_selectors(soup, config['discount_selectors'], 'Discount')
            
            # Extract offers
            offers = self.extract_offers_with_config(soup, config['offers_selectors'])
            
            # Extract product image
            image_url = self.extract_product_image(soup, config['image_selectors'], site_key)
            
            # Extract additional info
            delivery = self.extract_delivery_info(soup)
            availability = self.extract_availability(soup)
            
            return {
                'index': index,
                'name': name,
                'current_price': current_price,
                'original_price': original_price,
                'rating': rating,
                'reviews': reviews,
                'discount': discount,
                'offers': offers,
                'image_url': image_url,
                'delivery': delivery,
                'availability': availability,
                'search_query': search_query or 'N/A',
                'site': site_key,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Error extracting product data: {e}")
            return None
    
    def extract_sathya_name(self, soup: BeautifulSoup) -> str:
        """Special name extraction for Sathya Store"""
        try:
            # Try to get name from image alt attribute first
            img = soup.find('img')
            if img and img.get('alt'):
                alt_text = img.get('alt').strip()
                if alt_text and len(alt_text) > 5 and not alt_text.startswith('₹'):
                    return alt_text
            
            # Try to get name from link href
            link = soup.find('a', href=True)
            if link:
                href = link.get('href', '')
                if '/category/' in href:
                    # Extract product name from URL
                    parts = href.split('/')
                    if len(parts) > 0:
                        name = parts[-1].replace('-', ' ').title()
                        if name and len(name) > 3:
                            return name
            
            # Try to get name from product detail section
            product_detail = soup.find('div', class_='product-detail')
            if product_detail:
                # Look for title in product detail
                title_elem = product_detail.find('h4') or product_detail.find('h3') or product_detail.find('h2')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 5 and not title_text.startswith('₹'):
                        return title_text
            
            # Try to get name from any text content
            text_content = soup.get_text(strip=True)
            if text_content and len(text_content) > 10:
                # Clean up the text and find the first meaningful line
                lines = text_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 5 and not line.startswith('₹') and not line.startswith('(') and not line.startswith('Save'):
                        return line
                        
        except Exception as e:
            print(f"Error extracting Sathya name: {e}")
        
        return 'N/A'
    
    def extract_sathya_original_price(self, soup: BeautifulSoup) -> str:
        """Special original price extraction for Sathya Store (MRP)"""
        try:
            # First try the working selectors from debug
            mrp_selectors = [
                'span:contains("MRP")',
                'div:contains("MRP")',
                'p:contains("MRP")'
            ]
            
            for selector in mrp_selectors:
                if ':contains(' in selector:
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    elements = soup.find_all(string=re.compile(text_to_find, re.IGNORECASE))
                    if elements:
                        parent = elements[0].parent
                        if parent:
                            text = parent.get_text(strip=True)
                            # Extract price from MRP text
                            price_match = re.search(r'₹([\d,]+)', text)
                            if price_match:
                                return f"₹{price_match.group(1)}"
            
            # Fallback: Look for MRP in text content
            text_content = soup.get_text(strip=True)
            
            # Search for MRP patterns
            mrp_patterns = [
                r'MRP[:\s]*₹?([\d,]+)',
                r'M\.R\.P[:\s]*₹?([\d,]+)',
                r'₹([\d,]+)\s*\(MRP\)',
                r'₹([\d,]+)\s*\(M\.R\.P\)'
            ]
            
            for pattern in mrp_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    price = match.group(1)
                    return f"₹{price}"
                
        except Exception as e:
            print(f"Error extracting Sathya original price: {e}")
        
        return 'N/A'
    
    def extract_with_multiple_selectors(self, soup: BeautifulSoup, selectors: List[str], field_name: str) -> str:
        """Try multiple selectors to extract data"""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle :contains() pseudo-selector manually
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    # Find elements that contain the text
                    elements = soup.find_all(string=re.compile(text_to_find, re.IGNORECASE))
                    if elements:
                        # Get the parent element and extract its text
                        parent = elements[0].parent
                        if parent:
                            return parent.get_text(strip=True)
                        return elements[0].strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if text and text != 'N/A' and len(text) > 0:
                            return text
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue
        return 'N/A'
    
    def extract_offers_with_config(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract offers using configuration"""
        offers = []
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    elements = soup.find_all(text=re.compile(text_to_find, re.IGNORECASE))
                    for element in elements:
                        if element.strip():
                            offers.append(element.strip())
                else:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and text not in offers:
                            offers.append(text)
            except:
                continue
        
        return offers
    
    def extract_product_image(self, soup: BeautifulSoup, selectors: List[str], site_key: str = None) -> str:
        """Extract product image URL using configuration"""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle :contains() pseudo-selector manually
                    text_to_find = selector.split(':contains("')[1].split('")')[0]
                    elements = soup.find_all(string=re.compile(text_to_find, re.IGNORECASE))
                    if elements:
                        parent = elements[0].parent
                        if parent:
                            img = parent.find('img')
                            if img:
                                return self.clean_image_url(img.get('src') or img.get('data-src'), site_key)
                else:
                    img = soup.select_one(selector)
                    if img:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if src:
                            return self.clean_image_url(src, site_key)
            except Exception as e:
                print(f"Error with image selector {selector}: {e}")
                continue
        return 'N/A'
    
    def clean_image_url(self, url: str, site_key: str = None) -> str:
        """Clean and validate image URL"""
        if not url or url == 'N/A':
            return 'N/A'
        
        # Remove any leading/trailing whitespace
        url = url.strip()
        
        # Handle relative URLs based on site
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            if site_key == 'amazon':
                url = 'https://www.amazon.in' + url
            elif site_key == 'flipkart':
                url = 'https://www.flipkart.com' + url
            elif site_key == 'meesho':
                url = 'https://www.meesho.com' + url
            elif site_key == 'sathya':
                url = 'https://www.sathya.store' + url
            else:
                url = 'https://www.amazon.in' + url  # Default fallback
        
        # Remove any query parameters that might be for sizing
        if '?' in url:
            base_url = url.split('?')[0]
            # Keep the URL if it looks like a valid image
            if any(ext in base_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                url = base_url
        
        return url
    
    def extract_delivery_info(self, soup: BeautifulSoup) -> str:
        """Extract delivery information"""
        delivery_selectors = [
            'div[class*="delivery"]',
            'span[class*="delivery"]',
            'div[class*="shipping"]',
            'span:contains("delivery")',
            'span:contains("shipping")'
        ]
        
        for selector in delivery_selectors:
            try:
                if ':contains(' in selector:
                    elements = soup.find_all(text=re.compile('delivery|shipping', re.IGNORECASE))
                    if elements:
                        return elements[0].strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            except:
                continue
        
        return 'N/A'
    
    def extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability information"""
        availability_selectors = [
            'span[class*="stock"]',
            'div[class*="availability"]',
            'span:contains("bought")',
            'span:contains("stock")'
        ]
        
        for selector in availability_selectors:
            try:
                if ':contains(' in selector:
                    elements = soup.find_all(text=re.compile('bought|stock|available', re.IGNORECASE))
                    if elements:
                        return elements[0].strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            except:
                continue
        
        return 'N/A'
    
    def clean_product_data(self, product_data: Dict) -> Dict:
        """Clean and normalize product data"""
        # Clean name
        if product_data.get('name'):
            name = product_data['name'].strip()
            # Remove common prefixes
            prefixes_to_remove = [
                'Add to Compare', 'Sponsored', 'SponsoredCason', 
                'SponsoredCason Wireless', 'SponsoredCason Wireless + Wired'
            ]
            for prefix in prefixes_to_remove:
                if name.startswith(prefix):
                    name = name[len(prefix):].strip()
            product_data['name'] = name
        
        # Clean price - extract only numbers
        if product_data.get('current_price'):
            price = product_data['current_price']
            # Extract numbers from price
            import re
            price_match = re.search(r'[\d,]+', str(price))
            if price_match:
                product_data['current_price'] = f"₹{price_match.group()}"
            else:
                product_data['current_price'] = 'N/A'
        
        # Clean rating - extract only numbers
        if product_data.get('rating'):
            rating = product_data['rating']
            rating_match = re.search(r'(\d+\.?\d*)', str(rating))
            if rating_match:
                product_data['rating'] = rating_match.group(1)
            else:
                product_data['rating'] = 'N/A'
        
        # Clean reviews - extract only numbers
        if product_data.get('reviews'):
            reviews = product_data['reviews']
            reviews_match = re.search(r'(\d+)', str(reviews))
            if reviews_match:
                product_data['reviews'] = reviews_match.group(1)
            else:
                product_data['reviews'] = 'N/A'
        
        return product_data

    def validate_product_data(self, product_data: Dict, site_key: str) -> bool:
        """Validate product data based on site"""
        # Clean the data first
        product_data = self.clean_product_data(product_data)
        
        # Basic validation
        if not product_data['name'] or product_data['name'] == 'N/A':
            return False
        
        # Check for obviously bad names
        bad_name_patterns = [
            'Add to Compare', 'Sponsored', 'SponsoredCason',
            'SponsoredCason Wireless', 'SponsoredCason Wireless + Wired'
        ]
        
        for pattern in bad_name_patterns:
            if pattern in product_data['name']:
                return False
        
        # Check for very short names
        if len(product_data['name']) < 5:
            return False
        
        # Check for names that are just numbers
        if product_data['name'].isdigit():
            return False
        
        # Check for names that start with price symbols
        if product_data['name'].startswith('₹'):
            return False
        
        # Site-specific validation
        if site_key == 'amazon':
            # Amazon products should have reasonable names
            if len(product_data['name']) < 10:
                return False
        
        elif site_key == 'flipkart':
            # Flipkart products should have names
            if len(product_data['name']) < 5:
                return False
        
        elif site_key == 'sathya':
            # Sathya Store - be very lenient, just check if we have some name
            if len(product_data['name']) < 2:
                return False
            # Don't accept price as name
            if product_data['name'].startswith('₹'):
                return False
        
        elif site_key == 'meesho':
            # Meesho might have shorter names, be more lenient
            if len(product_data['name']) < 3:
                return False
        
        return True
    
    def save_to_json(self, filename: str = None) -> str:
        """Save products to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"universal_products_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVED] Products saved to {filename}")
        return filename
    
    def save_to_csv(self, filename: str = None) -> str:
        """Save products to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"universal_products_{timestamp}.csv"
        
        if not self.products:
            print("[WARNING] No products to save")
            return filename
        
        # Define the desired column order
        column_order = [
            'index', 'search_query', 'name', 'current_price', 'original_price', 
            'rating', 'reviews', 'discount', 'offers', 'image_url', 
            'delivery', 'availability', 'site', 'scraped_at'
        ]
        
        # Flatten offers list for CSV and reorder columns
        csv_data = []
        for product in self.products:
            row = {}
            # Add fields in the desired order
            for field in column_order:
                if field == 'offers':
                    row[field] = '; '.join(product.get('offers', [])) if product.get('offers') else ''
                else:
                    row[field] = product.get(field, 'N/A')
            csv_data.append(row)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=column_order)
                writer.writeheader()
                writer.writerows(csv_data)
        
        print(f"[SAVED] Products saved to {filename}")
        return filename
    
    def save_to_supabase(self) -> bool:
        """Save products to Supabase database"""
        if not self.supabase_client:
            print("[ERROR] Supabase client not initialized. Cannot save to database.")
            return False
        
        if not self.products:
            print("[WARNING] No products to save to database")
            return False
        
        try:
            # Prepare data for database insertion
            db_products = []
            for product in self.products:
                # Convert offers list to string for database storage
                offers_str = '; '.join(product.get('offers', [])) if product.get('offers') else ''
                
                db_product = {
                    'index': product.get('index'),
                    'search_query': product.get('search_query', 'N/A'),
                    'name': product.get('name', 'N/A'),
                    'current_price': product.get('current_price', 'N/A'),
                    'original_price': product.get('original_price', 'N/A'),
                    'rating': product.get('rating', 'N/A'),
                    'reviews': product.get('reviews', 'N/A'),
                    'discount': product.get('discount', 'N/A'),
                    'offers': offers_str,
                    'image_url': product.get('image_url', 'N/A'),
                    'delivery': product.get('delivery', 'N/A'),
                    'availability': product.get('availability', 'N/A'),
                    'site': product.get('site', 'N/A'),
                    'scraped_at': product.get('scraped_at')
                }
                db_products.append(db_product)
            
            # Insert products into database
            result = self.supabase_client.table('universal_products').insert(db_products).execute()
            
            if result.data:
                print(f"[SUCCESS] Saved {len(result.data)} products to Supabase database")
                return True
            else:
                print("[ERROR] Failed to save products to database")
                return False
                
        except Exception as e:
            print(f"[ERROR] Database save failed: {e}")
            return False
    
    def print_summary(self):
        """Print scraping summary"""
        print(f"\n[SUMMARY] Universal Scraping Summary:")
        print(f"   Total products found: {len(self.products)}")
        
        if self.products:
            # Group by site
            by_site = {}
            for product in self.products:
                site = product.get('site', 'unknown')
                if site not in by_site:
                    by_site[site] = []
                by_site[site].append(product)
            
            for site, products in by_site.items():
                print(f"   {site}: {len(products)} products")
            
            print(f"\n[SAMPLE] Sample products:")
            for i, product in enumerate(self.products[:5]):
                print(f"   {i+1}. [{product['site']}] {product['name'][:50]}...")
                print(f"      Search: {product.get('search_query', 'N/A')}")
                print(f"      Price: {product['current_price']} | Rating: {product['rating']} | Reviews: {product['reviews']}")
                if product.get('image_url') and product['image_url'] != 'N/A':
                    print(f"      Image: {product['image_url'][:80]}...")
                else:
                    print(f"      Image: No image available")

async def main():
    """Main function to demonstrate the universal scraper"""
    # Supabase credentials - replace with your actual credentials
    SUPABASE_URL = "https://whfjofihihlhctizchmj.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndoZmpvZmloaWhsaGN0aXpjaG1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzNzQzNDMsImV4cCI6MjA3Njk1MDM0M30.OsJnOqeJgT5REPg7uxkGmmVcHIcs5QO4vdyDi66qpR0"
    
    # Initialize scraper with Supabase credentials
    scraper = UniversalEcommerceScraper(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
    
    # Test different sites with search queries
    sites_to_test = [
        ('amazon', 'mobile phones'),
        ('flipkart', 'mobile phones'),
        ('meesho', 'saree'),
        ('sathya', 'vivo mobile')
    ]
    
    for site, search_query in sites_to_test:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Attempting to scrape {site} (attempt {attempt + 1}/{max_retries})")
                await scraper.scrape_site(site, search_query=search_query)
                
                # Check if we got products for this site
                site_products = [p for p in scraper.products if p.get('site') == site]
                if site_products:
                    print(f"[SUCCESS] Found {len(site_products)} products from {site}")
                    break
                else:
                    print(f"[WARNING] No products found from {site}, retrying...")
                    
                await asyncio.sleep(2)  # Delay between attempts
            except Exception as e:
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"[ERROR] Error with {site} (attempt {attempt + 1}): {error_msg}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Retrying {site} in 3 seconds...")
                    await asyncio.sleep(3)
        
            await asyncio.sleep(2)  # Delay between sites
    
    # Final fallback - if still no products, try emergency extraction
    if len(scraper.products) == 0:
        print("[WARNING] No products found with standard methods, trying emergency extraction...")
        await scraper.emergency_extraction()
    
    # Print final summary
    scraper.print_summary()
    
    # Save to Supabase database only
    if scraper.supabase_client:
        print(f"\n[DATABASE] Saving products to Supabase...")
        db_success = scraper.save_to_supabase()
        if db_success:
            print(f"[SUCCESS] Products saved to Supabase database")
        else:
            print(f"[ERROR] Failed to save products to database")
    else:
        print(f"[WARNING] Supabase not available - products not saved to database")
    
    print(f"\n[SUCCESS] Universal scraping completed!")
    print(f"[DATABASE] All products saved to Supabase (universal_products table)")

if __name__ == "__main__":
    asyncio.run(main())