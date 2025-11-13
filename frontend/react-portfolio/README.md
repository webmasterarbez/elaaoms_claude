# ELAAOMS Portfolio Website

A professional, modern React-based portfolio website to showcase and sell the ELAAOMS (ElevenLabs Agents Universal Agentic Open Memory System) project.

## 🎨 Design Features

This portfolio website is inspired by the Hexafolio template and includes:

- **Modern, Dark Theme**: Sleek dark design with gradient accents
- **Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- **Smooth Animations**: Subtle animations and transitions for professional feel
- **Interactive Components**: Tabbed code examples, hover effects, and smooth scrolling
- **SEO Optimized**: Proper meta tags and semantic HTML structure

## 📁 Project Structure

```
portfolio/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── components/
│   │   ├── Navbar.js          # Navigation bar
│   │   ├── Navbar.css
│   │   ├── Hero.js            # Hero/banner section
│   │   ├── Hero.css
│   │   ├── Features.js        # Features showcase
│   │   ├── Features.css
│   │   ├── HowItWorks.js      # Architecture & workflow
│   │   ├── HowItWorks.css
│   │   ├── CodeExample.js     # Interactive code examples
│   │   ├── CodeExample.css
│   │   ├── Pricing.js         # Pricing plans
│   │   ├── Pricing.css
│   │   ├── Documentation.js   # Documentation links
│   │   ├── Documentation.css
│   │   ├── Footer.js          # Footer with links
│   │   └── Footer.css
│   ├── App.js                 # Main app component
│   ├── App.css                # Main app styles
│   ├── index.js               # React entry point
│   └── index.css              # Global styles
├── package.json               # Dependencies
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

- Node.js 14.0 or higher
- npm or yarn

### Installation

1. **Navigate to the portfolio directory**:
   ```bash
   cd portfolio
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm start
   ```

4. **Open your browser**:
   Visit `http://localhost:3000` to see the website

### Build for Production

To create a production-ready build:

```bash
npm run build
```

This creates an optimized build in the `build/` directory, ready for deployment.

## 📄 Sections Overview

### 1. Hero Section
- Eye-catching headline with gradient text
- Clear value proposition
- Call-to-action buttons
- Key statistics (100% Automatic, <2s Response Time, ∞ Agents)
- Animated code preview

### 2. Features Section
- 8 key features with icons
- Automatic Memory Extraction
- Personalized Greetings
- Real-Time Memory Search
- Multi-Agent Support
- Zero Database Setup
- HMAC-SHA256 Security
- Background Processing
- Smart Deduplication

### 3. How It Works
- 3-step workflow explanation
- Pre-Call: Personalized Greeting
- During Call: Memory Search
- Post-Call: Memory Extraction
- System architecture diagram

### 4. Code Examples
- Interactive tabbed interface
- Quick Setup guide
- Webhook configuration examples
- Memory search examples
- Auto-extraction examples

### 5. Pricing
- 3 pricing tiers:
  - Open Source (Free)
  - Managed Hosting (Contact)
  - Enterprise (Custom)
- Clear feature comparison
- Usage cost transparency

### 6. Documentation
- Links to all documentation
- Memory System Guide
- Deployment Guide
- API Documentation
- Quick Start Guide
- Utility Scripts
- Code Analysis

### 7. Footer
- Product links
- Resource links
- Company information
- Social media links
- Copyright and license info

## 🎨 Customization

### Colors

Edit CSS variables in `src/index.css`:

```css
:root {
  --primary-color: #6366f1;
  --secondary-color: #8b5cf6;
  --accent-color: #ec4899;
  /* ... other colors */
}
```

### Content

Update content in individual component files:
- Hero text: `src/components/Hero.js`
- Features: `src/components/Features.js`
- Pricing: `src/components/Pricing.js`
- etc.

### Links

Update GitHub and external links in:
- `src/components/Hero.js` - CTA buttons
- `src/components/Navbar.js` - Navigation
- `src/components/Documentation.js` - Doc links
- `src/components/Footer.js` - Footer links

## 📱 Responsive Design

The website is fully responsive with breakpoints at:
- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: 320px - 767px

## ♿ Accessibility

- Semantic HTML elements
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus indicators
- Reduced motion support for users who prefer it

## 🌐 Deployment

### Deploy to Netlify

1. Push your code to GitHub
2. Connect your repository to Netlify
3. Build command: `npm run build`
4. Publish directory: `build`

### Deploy to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts

### Deploy to GitHub Pages

1. Install gh-pages: `npm install --save-dev gh-pages`
2. Add to `package.json`:
   ```json
   "homepage": "https://yourusername.github.io/elaaoms",
   "scripts": {
     "predeploy": "npm run build",
     "deploy": "gh-pages -d build"
   }
   ```
3. Run: `npm run deploy`

## 🔧 Technologies Used

- **React 18** - UI library
- **CSS3** - Styling with custom properties
- **React Icons** - Icon library
- **Framer Motion** - Animation library (optional)
- **React Router** - Navigation (optional)

## 📝 License

This portfolio website is part of the ELAAOMS project and is released under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💡 Tips

1. **Update Links**: Replace placeholder links (email, social media) with real ones
2. **Add Analytics**: Integrate Google Analytics or similar for tracking
3. **Add Contact Form**: Consider adding a contact form in the footer
4. **Optimize Images**: If you add images, optimize them for web
5. **SEO**: Update meta tags in `public/index.html` for better SEO

## 📞 Support

For issues or questions about the portfolio website, please open an issue on the main ELAAOMS repository.

---

Built with ❤️ to showcase ELAAOMS - The Universal Memory System for ElevenLabs Agents
