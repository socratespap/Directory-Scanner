# 📂 Directory Scanner

A high-performance directory scanner that finds, sorts, and previews the largest files on your hard drive. Built with Python and PyQt6 for a modern, user-friendly experience.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)

## 🚀 Features

- **⚡ High Performance**: Optimized Python implementation for fast scanning
- **🖥️ Modern GUI**: Beautiful PyQt6 interface with dark theme
- **📊 Smart Sorting**: Automatically sorts files by size (largest first)
- **🎯 File Type Filtering**: Filter by Images, Videos, Archives, and Executables
- **📈 Progress Tracking**: Real-time percentage-based progress bar
- **👀 File Preview**: Built-in text file preview functionality
- **🗑️ File Management**: Delete files and directories directly from the interface
- **📤 Export Results**: Save scan results to JSON format
- **🔄 Cross-Platform**: Works on Windows, Linux, and macOS
- **📦 Standalone Executable**: Ready-to-use .exe file included

## 📋 Prerequisites

### Required
- **Python 3.8+** with pip
- **PyQt6** for the GUI

## 🛠️ Installation

### 1. Clone or Download
```bash
git clone <repository-url>
cd "Directory Scanner"
```

### 2. Install Python Dependencies
```bash
cd python_frontend
pip install -r requirements.txt
```

### 3. You're Ready!
The application is now ready to use. You can either run the standalone executable or the Python script directly.

## 🎯 Usage

### Standalone Executable (Recommended)
```bash
# Navigate to the executable
cd "python_frontend"
# Run the standalone application
"Directory Scanner.exe"
```

### GUI Application (Development)
```bash
cd python_frontend
python main.py
```



## 📖 How to Use

1. **Launch the Application**
   - Double-click `Directory Scanner.exe` (standalone)
   - Or run `python main.py` (development)

2. **Select Directory**
   - Click "Browse" to select a directory
   - Or type the path directly

3. **Configure File Filters (Optional)**
   - Check "Images" for image files (.jpg, .png, .gif, etc.)
   - Check "Videos" for video files (.mp4, .avi, .mov, etc.)
   - Check "Archives" for compressed files (.zip, .rar, .7z, etc.)
   - Check "Executables" for executable files (.exe, .msi, .app, etc.)
   - Leave unchecked to scan all file types

4. **Configure Scan**
   - Choose max results (100-10,000 files pr Unlimited files)
   - Click "Start Scan"
   - Watch the real-time progress bar

5. **View Results**
   - Files are automatically sorted by size
   - Click any file to preview its contents
   - Use the table headers to sort by different criteria

6. **Export Results**
   - Click "Export Results" to save as JSON
   - Choose your preferred location

## 🏗️ Project Structure

```
Directory Scanner/
├── 📄 README.md                  # This file
├── 📄 run.bat                    # Windows batch script
├── 📄 run.sh                     # Unix shell script
├── 📄 test_scanner.py            # Test utilities
└── 📁 python_frontend/           # PyQt6 GUI application
    ├── 📄 Directory Scanner.exe  # Standalone executable (ready to use)
    ├── 📄 main.exe              # Build artifact
    ├── 📄 requirements.txt      # Python dependencies
    ├── 📄 main.py              # Main GUI application
    ├── 📄 main.spec            # PyInstaller configuration
    ├── 📁 build/               # Build artifacts
    └── 📁 dist/                # Distribution files
```

## ⚙️ Configuration

### Performance Tuning

**Python Implementation:**
- Optimized file system operations
- Efficient memory usage
- Real-time progress tracking
- Suitable for directories of all sizes

### Customization

Edit `python_frontend/main.py` to customize:
- Default scan limits
- UI themes and colors
- File preview formats
- Export options

## 🔧 Building for Distribution

### Create Standalone Executables

**Python Application:**
```bash
cd python_frontend
pip install pyinstaller
pyinstaller --onefile --windowed main.py
# Executable: dist/main.exe (Windows)
```

### Cross-Platform Builds

**Windows:**
```bash
pyinstaller --onefile --windowed main.py
```

**Linux:**
```bash
pyinstaller --onefile --windowed main.py
```

**macOS:**
```bash
pyinstaller --onefile --windowed main.py
```

## 🐛 Troubleshooting

### Common Issues



**"No module named 'PyQt6'"**
```bash
pip install PyQt6
```

**"Permission denied" errors**
- Run as administrator (Windows) or with sudo (Linux/macOS)
- Check directory permissions

**Slow scanning performance**
- Reduce the max results limit
- Scan smaller directory trees
- Close other applications to free up system resources

### Performance Comparison

| Directory Size | Scan Time | Memory Usage |
|---------------|-----------|-------------|
| Small (1K files) | ~1 second | ~30MB |
| Medium (10K files) | ~5 seconds | ~50MB |
| Large (100K files) | ~30 seconds | ~100MB |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
cd python_frontend
pip install -r requirements.txt
pip install pytest black flake8

# Format code
black main.py

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PyQt6** for the excellent GUI framework
- **Python Community** for amazing libraries and tools
- **PyInstaller** for making standalone executables possible

## 📊 Roadmap

- [x] Add file type filtering (Images, Videos, Archives, Executables)
- [x] Real-time progress tracking with percentage display
- [x] Standalone executable distribution
- [x] Modern dark theme UI
- [ ] Implement duplicate file detection
- [ ] Add directory size visualization
- [ ] Create installer packages
- [ ] Add network drive support
- [x] Implement file operations (delete files and directories)
- [ ] Add file hash calculation
- [ ] Implement search functionality

---

**Made with ❤️ using Python**

*This app is created by [https://socratisp.com](https://socratisp.com)*