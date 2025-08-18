# DocTags Analyzer and Visualizer

AI-powered document analysis and visualization tool for extracting structured content from PDFs.

<img width="800" height="685" alt="image" src="https://github.com/user-attachments/assets/ce301175-ea4b-42e8-8e3a-ff9c326b84cd" />


## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB of free memory
- ~500MB disk space for the AI model

### Running with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SmolDocling-visualizer
   ```

2. **Place your PDF files in the project directory**
   ```bash
   cp /path/to/your/document.pdf ./
   ```

3. **Start the application**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the web interface**
   - Open http://localhost:8080 in your browser
   - Select a PDF from the dropdown
   - Process your documents through the three-step workflow

### First Run Notice
⚠️ **Important**: The first analysis will take 5-10 minutes as the AI model (SmolDocling-256M) needs to be downloaded (~500MB). Subsequent runs will be much faster (30-60 seconds).

## 📋 Features

- **Document Analysis**: Extract comprehensive document structure using AI
- **Visualization**: Generate visual overlays showing document elements
- **Image Extraction**: Automatically extract and catalog embedded images
- **Web Interface**: User-friendly interface for document processing

## 🛠️ Manual Usage

Process PDF pages with DocTags:

```bash
python analyzer.py --image document.pdf --page 8 && python visualizer.py --doctags results/output.doctags.txt --pdf document.pdf --page 8 --adjust && python picture_extractor.py --doctags results/output.doctags.txt --pdf document.pdf --page 8 --adjust
```

## 🐛 Troubleshooting

### Docker Issues

1. **Container won't start**
   - Check logs: `docker-compose logs analyser`
   - Ensure ports aren't in use: `lsof -i :8080`

2. **"No module named 'docling_core'" error**
   - Rebuild the container: `docker-compose down && docker-compose up -d --build`

3. **Analysis stuck on "Running..."**
   - First run downloads the AI model (~500MB), this can take 5-10 minutes
   - Check progress: `docker-compose exec analyser du -sh /root/.cache/huggingface/`
   - Monitor CPU usage: `docker-compose exec analyser ps aux | grep analyzer`

4. **PDF not loading**
   - Ensure poppler is installed (already included in Dockerfile)
   - Place PDFs in the project root directory
   - PDFs must have `.pdf` extension

### Performance Tips

- First analysis is slow due to model download
- Subsequent analyses are much faster (model is cached)
- Processing time depends on PDF complexity and page size
- Monitor memory usage: `docker-compose exec analyser free -h`

## 📁 Project Structure

```
doc-analyzer/
├── backend/
│   ├── page_treatment/     # Core processing scripts
│   │   ├── analyzer.py     # AI-powered document analysis
│   │   ├── visualizer.py   # Visualization generator
│   │   └── picture_extractor.py  # Image extraction
│   ├── app.py             # Flask web application
│   └── requirements.txt   # Python dependencies
├── frontend/              # Web interface
├── results/              # Output directory (auto-created)
├── Dockerfile           # Docker configuration
└── docker-compose.yml   # Docker Compose setup
```

## 🔧 Development

To modify the application:

1. Make changes to the code
2. Rebuild the Docker image: `docker-compose up -d --build`
3. Check logs for errors: `docker-compose logs -f analyser`

## 📄 License

This project is open source and available under the MIT License.
