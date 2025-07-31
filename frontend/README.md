# LabelTool Frontend

A modern React application for intelligent text detection and removal from images.

## Features

- 🎨 **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- 🖼️ **Interactive Canvas**: Powered by Konva.js for smooth image manipulation
- 🔍 **Text Detection**: Automatic text region detection with PaddleOCR
- ✏️ **Manual Editing**: Intuitive drag-and-drop region adjustment
- 🎯 **Smart Removal**: Advanced inpainting algorithms preserve background textures
- 📱 **Responsive Design**: Works on desktop and tablet devices
- 🌙 **Dark Mode**: Full dark mode support
- ⚡ **Performance**: Optimized with Zustand state management

## Tech Stack

- **React 18** - Modern UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Konva.js** - 2D canvas library for interactive graphics
- **Zustand** - Lightweight state management
- **React Dropzone** - File upload with drag-and-drop
- **Axios** - HTTP client for API communication
- **Lucide React** - Beautiful SVG icons

## Prerequisites

- Node.js 16 or higher
- npm or yarn
- Backend API running on port 8000

## Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173`

## Development Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Run tests
npm run test
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Base UI components (Button, Card, etc.)
│   ├── FileUpload/     # File upload component
│   ├── ImageCanvas/    # Interactive image canvas
│   ├── Toolbar/        # Main toolbar with actions
│   └── ...
├── hooks/              # Custom React hooks
├── services/           # API services
├── stores/             # Zustand state management
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── App.tsx             # Main application component
```

## Key Components

### FileUpload
- Drag-and-drop file upload
- File validation and progress tracking
- Support for JPEG, PNG, WebP formats
- Maximum file size: 10MB

### ImageCanvas
- Interactive image display with zoom and pan
- Text region visualization and selection
- Drag handles for region resizing
- Keyboard shortcuts for common actions

### Toolbar
- File management actions
- Canvas controls (zoom, fit to view)
- Processing and download buttons
- Status indicators

## Keyboard Shortcuts

- `Ctrl/Cmd + Plus` - Zoom in
- `Ctrl/Cmd + Minus` - Zoom out
- `Ctrl/Cmd + 0` - Reset zoom
- `Ctrl/Cmd + P` - Process text removal
- `Ctrl/Cmd + D` - Download result
- `Escape` - Deselect region
- `Delete/Backspace` - Delete selected region

## API Integration

The frontend communicates with the FastAPI backend through RESTful endpoints:

- `POST /api/v1/sessions` - Upload image and create session
- `GET /api/v1/sessions/{id}` - Get session details
- `PUT /api/v1/sessions/{id}/regions` - Update text regions
- `POST /api/v1/sessions/{id}/process` - Process text removal
- `GET /api/v1/sessions/{id}/result` - Download processed image

## State Management

Uses Zustand for efficient state management:

- **Session State**: Current session and image data
- **Canvas State**: Zoom, pan, and selection state
- **UI State**: Loading states, errors, and user preferences
- **Persistent Storage**: Settings and canvas preferences

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **CSS Variables**: Dark mode support with CSS custom properties
- **Component Variants**: Class Variance Authority for consistent styling
- **Custom Animations**: Smooth transitions and loading states

## Performance Optimizations

- **Code Splitting**: Automatic route-based code splitting
- **Image Optimization**: Efficient canvas rendering with Konva
- **State Optimization**: Minimal re-renders with Zustand
- **Debounced Updates**: Smooth interaction without performance issues

## Browser Support

- Chrome/Edge 88+
- Firefox 78+
- Safari 14+

## Troubleshooting

### Common Issues

1. **Canvas not displaying**
   - Check if backend API is running
   - Verify image upload was successful
   - Check browser console for errors

2. **Upload fails**
   - Ensure file is under 10MB
   - Check file format (JPEG, PNG, WebP only)
   - Verify backend is accessible

3. **Slow performance**
   - Try reducing image size
   - Check available system memory
   - Use hardware acceleration if available

### Development Tips

- Use browser dev tools for debugging
- Check Network tab for API errors
- Enable React Developer Tools for state inspection
- Use `npm run lint` to catch code issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.