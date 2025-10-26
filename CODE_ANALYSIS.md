# Universal E-commerce Scraper - Code Analysis

## Overview
This is a comprehensive Python-based web scraper designed to extract product information from multiple e-commerce platforms including Amazon, Flipkart, Meesho, and Sathya Store.

## Core Dependencies Analysis

### Primary Libraries
1. **crawl4ai** (v0.7.6) - Advanced web crawling framework
2. **beautifulsoup4** (v4.12.2) - HTML/XML parsing
3. **supabase** (v2.22.2) - Database integration (optional)
4. **lxml** (v5.4.0) - XML/HTML parser backend
5. **requests** (v2.31.0) - HTTP library
6. **aiohttp** (v3.13.1) - Async HTTP client/server
7. **asyncio** (v4.0.0) - Asynchronous I/O support

### Secondary Dependencies (Auto-installed)
- **aiofiles** (v25.1.0) - Async file operations
- **aiosqlite** (v0.21.0) - Async SQLite support
- **anyio** (v4.11.0) - Async compatibility layer
- **litellm** (v1.78.7) - LLM integration
- **numpy** (v2.1.0) - Numerical computing
- **pillow** (v10.4.0) - Image processing
- **playwright** (v1.55.0) - Browser automation
- **patchright** (v1.55.2) - Playwright patches
- **python-dotenv** (v1.0.0) - Environment variables
- **tf-playwright-stealth** (v1.2.0) - Stealth browsing
- **xxhash** (v3.6.0) - Fast hashing
- **rank-bm25** (v0.2.2) - Text ranking
- **snowballstemmer** (v2.2.0) - Text stemming
- **pydantic** (v2.11.9) - Data validation
- **pyOpenSSL** (v25.2.0) - SSL/TLS support
- **psutil** (v7.0.0) - System monitoring
- **PyYAML** (v6.0.2) - YAML parsing
- **nltk** (v3.9.2) - Natural language processing
- **rich** (v13.9.4) - Rich text formatting
- **cssselect** (v1.3.0) - CSS selector support
- **httpx** (v0.28.1) - Modern HTTP client
- **fake-useragent** (v2.2.0) - User agent generation
- **click** (v8.1.7) - CLI framework
- **chardet** (v5.2.0) - Character encoding detection
- **brotli** (v1.1.0) - Compression support
- **humanize** (v4.14.0) - Human-readable formatting
- **lark** (v1.3.0) - Parsing toolkit
- **alphashape** (v1.3.1) - Geometric algorithms
- **shapely** (v2.1.2) - Geometric operations
- **soupsieve** (v2.6) - CSS selector for BeautifulSoup

### Database Dependencies (Supabase)
- **realtime** (v2.22.2) - Real-time subscriptions
- **supabase-functions** (v2.22.2) - Edge functions
- **storage3** (v2.22.2) - File storage
- **supabase-auth** (v2.22.2) - Authentication
- **postgrest** (v2.22.2) - PostgreSQL REST API

## Code Structure Analysis

### Main Class: UniversalEcommerceScraper
- **Purpose**: Central orchestrator for multi-site scraping
- **Key Features**:
  - Site-specific configuration management
  - Async web crawling with retry logic
  - Multiple parsing strategies (standard, alternative, aggressive)
  - Data validation and cleaning
  - Export to JSON/CSV formats

### Site Configurations
1. **Amazon India**: Complex product selectors, price extraction
2. **Flipkart**: Dynamic content handling, rating extraction
3. **Meesho**: Fashion-focused selectors, discount detection
4. **Sathya Store**: Electronics-focused, MRP extraction

### Parsing Strategies
1. **Standard Parsing**: Uses configured selectors
2. **Alternative Parsing**: Fallback selectors when standard fails
3. **Aggressive Parsing**: Text-based extraction from content
4. **Emergency Extraction**: Basic product creation when all else fails

### Data Extraction Features
- Product names with site-specific validation
- Price extraction (current and original)
- Rating and review count extraction
- Discount percentage calculation
- Offer/coupon detection
- Image URL extraction and cleaning
- Delivery and availability information

### Error Handling
- Comprehensive try-catch blocks
- Retry mechanisms with exponential backoff
- Graceful degradation when sites fail
- Unicode encoding handling for Windows

### Output Formats
- **JSON**: Structured data with all fields
- **CSV**: Tabular format for spreadsheet analysis
- **Console**: Real-time progress and summary

## Performance Considerations
- Async/await pattern for concurrent operations
- Configurable wait times and retry limits
- Memory-efficient parsing with BeautifulSoup
- Chunked processing for large datasets

## Security Features
- User agent rotation
- Stealth browsing capabilities
- Rate limiting between requests
- Error message sanitization

## Installation Status
✅ All dependencies successfully installed
✅ No version conflicts detected
✅ Import tests passed
✅ Ready for execution

## Usage
```bash
python products.py
```

The script will automatically scrape all configured sites and save results to timestamped JSON and CSV files.
