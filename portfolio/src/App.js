import React, { useState, useEffect } from 'react';
import './App.css';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import HowItWorks from './components/HowItWorks';
import CodeExample from './components/CodeExample';
import Pricing from './components/Pricing';
import Documentation from './components/Documentation';
import Footer from './components/Footer';

function App() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="App">
      <Navbar scrolled={scrolled} />
      <Hero />
      <Features />
      <HowItWorks />
      <CodeExample />
      <Pricing />
      <Documentation />
      <Footer />
    </div>
  );
}

export default App;
