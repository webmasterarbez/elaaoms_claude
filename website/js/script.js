// ===================================
// Navigation Scroll Effect
// ===================================
const navbar = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('nav-menu');

window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// ===================================
// Mobile Navigation Toggle
// ===================================
hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    hamburger.classList.toggle('active');
});

// Close mobile menu when clicking on a link
navMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
    });
});

// ===================================
// Particles Animation
// ===================================
function createParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = Math.random() * 4 + 1 + 'px';
        particle.style.height = particle.style.width;
        particle.style.background = `rgba(99, 102, 241, ${Math.random() * 0.5 + 0.2})`;
        particle.style.borderRadius = '50%';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.pointerEvents = 'none';

        // Animation
        const duration = Math.random() * 20 + 10;
        const delay = Math.random() * 5;
        particle.style.animation = `float ${duration}s ${delay}s infinite ease-in-out`;

        particlesContainer.appendChild(particle);
    }
}

// Add floating animation CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 0.3;
        }
        25% {
            transform: translate(20px, -30px) scale(1.1);
            opacity: 0.6;
        }
        50% {
            transform: translate(-15px, -60px) scale(0.9);
            opacity: 0.4;
        }
        75% {
            transform: translate(25px, -40px) scale(1.05);
            opacity: 0.5;
        }
    }
`;
document.head.appendChild(style);

createParticles();

// ===================================
// FAQ Accordion
// ===================================
const faqItems = document.querySelectorAll('.faq-item');

faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');

    question.addEventListener('click', () => {
        // Close other items
        faqItems.forEach(otherItem => {
            if (otherItem !== item) {
                otherItem.classList.remove('active');
            }
        });

        // Toggle current item
        item.classList.toggle('active');
    });
});

// ===================================
// Cost Calculator
// ===================================
const monthlyCallsInput = document.getElementById('monthlyCallsInput');
const hostedCostEl = document.getElementById('hostedCost');
const elaaomsCostEl = document.getElementById('elaaomsCost');
const savingsEl = document.getElementById('savings');

function calculateCosts() {
    const calls = parseInt(monthlyCallsInput.value) || 0;

    // Hosted services: $0.15 - $0.50 per call
    const hostedMin = calls * 0.15;
    const hostedMax = calls * 0.50;

    // ELAAOMS: $0.026 per call
    const elaaoms = calls * 0.026;

    // Savings
    const savingsMin = hostedMin - elaaoms;
    const savingsMax = hostedMax - elaaoms;

    // Format and display
    hostedCostEl.textContent = `$${hostedMin.toLocaleString()} - $${hostedMax.toLocaleString()}`;
    elaaomsCostEl.textContent = `$${elaaoms.toLocaleString()}`;
    savingsEl.textContent = `$${savingsMin.toLocaleString()} - $${savingsMax.toLocaleString()}`;
}

monthlyCallsInput.addEventListener('input', calculateCosts);

// Initial calculation
calculateCosts();

// ===================================
// Scroll to Top Button
// ===================================
const scrollTopBtn = document.getElementById('scrollTop');

window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        scrollTopBtn.classList.add('visible');
    } else {
        scrollTopBtn.classList.remove('visible');
    }
});

scrollTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// ===================================
// Smooth Scroll for Anchor Links
// ===================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');

        // Don't prevent default for empty hash or just #
        if (href === '#' || href === '') {
            return;
        }

        e.preventDefault();

        const target = document.querySelector(href);
        if (target) {
            const offsetTop = target.offsetTop - 80; // Account for fixed navbar

            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// ===================================
// Intersection Observer for Animations
// ===================================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all feature cards, pricing cards, etc.
const animateElements = document.querySelectorAll('.feature-card, .pricing-card, .timeline-item, .roadmap-item');
animateElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// ===================================
// Dynamic Stats Counter
// ===================================
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16); // 60 FPS

    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = formatStatNumber(target);
            clearInterval(timer);
        } else {
            element.textContent = formatStatNumber(Math.floor(start));
        }
    }, 16);
}

function formatStatNumber(num) {
    if (typeof num === 'string') return num;
    return num.toLocaleString();
}

// Trigger counter animation when stats come into view
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const originalText = stat.textContent;
                // Only animate if it's a pure number
                if (!isNaN(parseInt(originalText))) {
                    const target = parseInt(originalText);
                    animateCounter(stat, target);
                }
            });
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) {
    statsObserver.observe(heroStats);
}

// ===================================
// Code Block Copy Functionality
// ===================================
const codeBlocks = document.querySelectorAll('.code-block');

codeBlocks.forEach(block => {
    // Create copy button
    const copyBtn = document.createElement('button');
    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
    copyBtn.style.cssText = `
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(99, 102, 241, 0.2);
        border: 1px solid rgba(99, 102, 241, 0.5);
        color: #818cf8;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    `;

    block.style.position = 'relative';
    block.appendChild(copyBtn);

    copyBtn.addEventListener('click', async () => {
        const code = block.querySelector('code').textContent;

        try {
            await navigator.clipboard.writeText(code);
            copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            copyBtn.style.background = 'rgba(16, 185, 129, 0.2)';
            copyBtn.style.borderColor = 'rgba(16, 185, 129, 0.5)';
            copyBtn.style.color = '#10b981';

            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                copyBtn.style.background = 'rgba(99, 102, 241, 0.2)';
                copyBtn.style.borderColor = 'rgba(99, 102, 241, 0.5)';
                copyBtn.style.color = '#818cf8';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    });

    copyBtn.addEventListener('mouseenter', () => {
        if (!copyBtn.innerHTML.includes('Copied')) {
            copyBtn.style.background = 'rgba(99, 102, 241, 0.3)';
        }
    });

    copyBtn.addEventListener('mouseleave', () => {
        if (!copyBtn.innerHTML.includes('Copied')) {
            copyBtn.style.background = 'rgba(99, 102, 241, 0.2)';
        }
    });
});

// ===================================
// Page Load Animation
// ===================================
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease';

    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});

// ===================================
// Easter Egg: Konami Code
// ===================================
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.key);
    konamiCode = konamiCode.slice(-10);

    if (konamiCode.join('') === konamiSequence.join('')) {
        // Easter egg activated!
        document.body.style.animation = 'rainbow 2s linear infinite';

        const easterEggStyle = document.createElement('style');
        easterEggStyle.textContent = `
            @keyframes rainbow {
                0% { filter: hue-rotate(0deg); }
                100% { filter: hue-rotate(360deg); }
            }
        `;
        document.head.appendChild(easterEggStyle);

        setTimeout(() => {
            document.body.style.animation = '';
        }, 5000);
    }
});

// ===================================
// Analytics Event Tracking (Optional)
// ===================================
function trackEvent(eventName, eventData = {}) {
    // If you integrate Google Analytics or other analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, eventData);
    }
    console.log('Event tracked:', eventName, eventData);
}

// Track CTA clicks
document.querySelectorAll('.btn-primary, .btn-secondary').forEach(button => {
    button.addEventListener('click', (e) => {
        const buttonText = e.target.textContent.trim();
        const buttonHref = e.target.getAttribute('href');
        trackEvent('cta_click', {
            button_text: buttonText,
            button_url: buttonHref
        });
    });
});

// Track scroll depth
let maxScroll = 0;
const scrollMilestones = [25, 50, 75, 100];
const trackedMilestones = new Set();

window.addEventListener('scroll', () => {
    const scrollPercentage = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;

    if (scrollPercentage > maxScroll) {
        maxScroll = scrollPercentage;

        scrollMilestones.forEach(milestone => {
            if (scrollPercentage >= milestone && !trackedMilestones.has(milestone)) {
                trackedMilestones.add(milestone);
                trackEvent('scroll_depth', { percentage: milestone });
            }
        });
    }
});

// ===================================
// Console Message
// ===================================
console.log(
    '%cELAAOMS 🧠',
    'font-size: 24px; font-weight: bold; color: #6366f1;'
);
console.log(
    '%cUniversal Memory for Voice AI Agents',
    'font-size: 14px; color: #94a3b8;'
);
console.log(
    '%cInterested in contributing? Check out: https://github.com/webmasterarbez/elaaoms_claude',
    'font-size: 12px; color: #10b981;'
);
