# React Dashboard - Developer Guide

## Overview

This is the main React dashboard for the Network Observability system.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Tailwind CSS v4** - Styling
- **Shadcn UI** - Component library
- **Recharts** - Data visualization

## Development

### Setup
```bash
# Install dependencies
npm install

# Start dev server (with HMR)
npm run dev
# Visit http://localhost:5173
```

### Build for Production
```bash
# Build optimized bundle
npm run build

# Output goes to: dist/
```

### Preview Production Build
```bash
npm run preview
```

## Project Structure

```
react_dashboard/
├── src/
│   ├── api/
│   │   └── client.ts          # API client for backend
│   ├── components/
│   │   └── ui/                # Shadcn UI components
│   ├── lib/
│   │   └── utils.ts           # Utility functions
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main dashboard with charts
│   │   ├── AIAnalysis.tsx     # Agent control & analysis
│   │   ├── Controls.tsx       # Scenarios & logs
│   │   └── PhoenixTraces.tsx  # Observability view
│   ├── App.tsx                # Main app component
│   └── main.tsx               # Entry point
│
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript config
├── vite.config.ts             # Vite config
└── tailwind.config.ts         # Tailwind config
```

## Key Features

### Pages

1. **Dashboard** (`/`)
   - Real-time risk wave chart
   - AP status cards
   - Network health metrics

2. **AI Analysis** (`/analysis`)
   - Agent connection controls
   - Analysis results display
   - Real-time agent status

3. **Controls** (`/controls`)
   - Scenario simulation
   - Agent log viewer
   - Network scenarios

4. **Phoenix Traces** (`/phoenix`)
   - Embedded Phoenix dashboard
   - Trace analysis
   - Evaluation metrics

### API Integration

All API calls go through `src/api/client.ts`:

```typescript
// Example: Fetch risk scores
const data = await getRiskScores();

// Example: Start agents
await startSystem();
```

**Backend URL:** http://localhost:8000

## Development Tips

### Hot Module Replacement (HMR)
Vite provides instant updates when you save files. No need to refresh!

### TypeScript Errors
```bash
# Check for type errors
npm run tsc
```

### Adding New Components
```bash
# Use Shadcn CLI to add components
npx shadcn@latest add <component-name>
```

### Environment Variables
Create `.env.local` for local overrides:
```env
VITE_API_URL=http://localhost:8000
```

## Common Tasks

### Add a New Page
1. Create file in `src/pages/`
2. Add route in `App.tsx`
3. Add navigation in Dashboard layout

### Add a New Chart
1. Use Recharts components
2. Follow pattern in `Dashboard.tsx`
3. Style with Tailwind classes

### Connect to New API Endpoint
1. Add function to `src/api/client.ts`
2. Define TypeScript types
3. Use in component with error handling

## Building for Production

The build process:
1. **Optimizes** code with tree-shaking
2. **Minifies** JavaScript and CSS
3. **Chunks** code for better caching
4. **Outputs** to `dist/`

The backend serves these files automatically from `dist/`.

## Troubleshooting

### "Module not found"
```bash
rm -rf node_modules package-lock.json
npm install
```

### Build Fails
```bash
# Clear cache
rm -rf node_modules/.vite
npm run build
```

### Port 5173 in Use
```bash
# Kill process on port
npx kill-port 5173
```

## Performance

- **Code Splitting:** Automatic with Vite
- **Lazy Loading:** Use `React.lazy()` for heavy components
- **Memoization:** Use `React.memo()` for expensive renders

## Testing (Future)

```bash
# Will be added:
npm run test
npm run test:coverage
```

## Contributing

1. Follow existing code style
2. Use TypeScript types
3. Add comments for complex logic
4. Test in both dev and production builds

---

**Note:** This dashboard is served by the FastAPI backend in production. During development, you can run it standalone with `npm run dev`.
