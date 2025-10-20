// 3D Interaction Enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Skip 3D effects on analysis page
    const isAnalysisPage = window.location.pathname.includes('/analysis');
    
    // Add 3D tilt effect to cards on mouse move (except on analysis page)
    const cardSelector = isAnalysisPage ? '.card-stat, .forecast-stats' : '.card, .card-stat, .insight-card, .forecast-stats';
    const cards = document.querySelectorAll(cardSelector);
    
    cards.forEach(card => {
        // Store original transform
        let isHovering = false;
        
        card.addEventListener('mousemove', function(e) {
            if (!isHovering) return;
            
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-15px) scale(1.02)`;
        });
        
        card.addEventListener('mouseenter', function() {
            isHovering = true;
        });
        
        card.addEventListener('mouseleave', function() {
            isHovering = false;
            card.style.transform = '';
        });
    });
    
    // Add stagger animation to feature items
    const features = document.querySelectorAll('.feature-item');
    features.forEach((feature, index) => {
        feature.style.opacity = '0';
        feature.style.transform = 'translateY(30px)';
        setTimeout(() => {
            feature.style.transition = 'all 0.6s ease';
            feature.style.opacity = '1';
            feature.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Add reveal animation on scroll using IntersectionObserver (no transform conflicts)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
            }
        });
    }, observerOptions);
    
    // Observe all cards and sections
    document.querySelectorAll('.card, .row').forEach(el => {
        if (!el.classList.contains('revealed')) {
            observer.observe(el);
        }
    });
    
    // Navbar hide/show on scroll with throttling
    let lastScroll = 0;
    let ticking = false;
    const navbar = document.querySelector('.navbar');
    
    function updateNavbar() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > lastScroll && currentScroll > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(updateNavbar);
            ticking = true;
        }
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
});

// Add CSS for reveal animation and ripple effect
const style = document.createElement('style');
style.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .navbar {
        transition: transform 0.3s ease;
    }
    
    /* Reveal animation using class instead of inline styles */
    .card:not(.revealed), .row:not(.revealed) {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.8s cubic-bezier(0.23, 1, 0.320, 1);
    }
    
    .card.revealed, .row.revealed {
        opacity: 1;
        transform: translateY(0);
    }
`;
document.head.appendChild(style);
