// DOM Elements
const topicInput = document.getElementById('topicInput');
const findButton = document.getElementById('findButton');
const errorMessage = document.getElementById('errorMessage');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const btnText = findButton.querySelector('.btn-text');
const btnLoader = findButton.querySelector('.btn-loader');

// API Configuration
const API_BASE_URL = 'https://n6pj8blr56.execute-api.eu-north-1.amazonaws.com/recommend/';

// State Management
let isLoading = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    initializeApp();
    
    // Test if elements are found
    console.log('Topic Input:', topicInput);
    console.log('Find Button:', findButton);
    console.log('Elements initialized');
});

function initializeApp() {
    // Add event listeners with proper error handling
    if (findButton) {
        findButton.addEventListener('click', handleSearch);
        console.log('Click listener added to find button');
    }
    
    if (topicInput) {
        topicInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !isLoading) {
                handleSearch();
            }
        });
        
        // Clear error message when user starts typing
        topicInput.addEventListener('input', clearError);
        
        // Add input focus effects
        topicInput.addEventListener('focus', function() {
            console.log('Input focused');
            const parent = this.closest('.input-container');
            if (parent) {
                parent.style.transform = 'translateY(-2px)';
            }
        });
        
        topicInput.addEventListener('blur', function() {
            console.log('Input blurred');
            const parent = this.closest('.input-container');
            if (parent) {
                parent.style.transform = 'translateY(0)';
            }
        });
        
        console.log('Input listeners added');
    }
    
    // Add interactive background effects
    setTimeout(addInteractiveEffects, 1000);
}

function handleSearch() {
    console.log('Search button clicked');
    
    if (isLoading) {
        console.log('Already loading, skipping...');
        return;
    }
    
    const topic = topicInput.value.trim();
    console.log('Topic entered:', topic);
    
    // Validate input
    if (!topic) {
        showError('Please enter a topic you want to learn about.');
        topicInput.focus();
        return;
    }
    
    // Clear previous results and errors
    clearError();
    hideResults();
    
    // Start loading
    setLoadingState(true);
    
    // Make API call
    fetchArticleSummaries(topic);
}

async function fetchArticleSummaries(topic) {
    console.log('Fetching summaries for:', topic);
    
    try {
        const encodedTopic = encodeURIComponent(topic);
        const apiUrl = `${API_BASE_URL}${encodedTopic}`;
        console.log('API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API Response:', data);
        
        // Parse the response
        const summaries = parseApiResponse(data);
        console.log('Parsed summaries:', summaries);
        
        if (summaries && summaries.length > 0) {
            displayResults(summaries);
        } else {
            throw new Error('No summaries found in the response.');
        }
        
    } catch (error) {
        console.error('Error fetching articles:', error);
        showError(getErrorMessage(error));
    } finally {
        setLoadingState(false);
    }
}

function parseApiResponse(data) {
    try {
        if (!data || !data.agent_content) {
            throw new Error('Invalid response format');
        }
        
        // Parse the JSON array from the agent_content string
        
        
        // Skip the first element (count) and take the next 3 summaries
        const summaries = data.agent_content.slice(1, 4);
        
        return summaries
        
    } catch (error) {
        console.error('Error parsing response:', error);
        throw new Error('Failed to parse article summaries');
    }
}

function displayResults(summaries) {
    console.log('Displaying results:', summaries);
    
    // Clear previous results
    resultsGrid.innerHTML = '';
    
    // Create cards for each summary
    summaries.forEach((summary, index) => {
        const card = createArticleCard(summary, index);
        resultsGrid.appendChild(card);
    });
    
    // Show results section with animation
    showResults();
}

function createArticleCard(summary, index) {
    const card = document.createElement('div');
    card.className = 'article-card glass-card';
    card.style.animationDelay = `${index * 0.1}s`;
    
    // Parse the summary content into sections
    const sections = summary;
    
    card.innerHTML = `
        <h4>${summary.title}</ht>
        <div class="card-content">
            ${sections.introduction ? `
                <div class="card-section">
                    <h3 class="section-title">Introduction</h3>
                    <p class="section-content">${escapeHtml(sections.introduction??"abc")}</p>
                </div>
            ` : ''}
            
            ${sections.bodyHighlights ? `
                <div class="card-section">
                    <h3 class="section-title">Body Highlights</h3>
                    <p class="section-content">${escapeHtml(sections.bodyHighlights??"def")}</p>
                </div>
            ` : ''}
            
            ${sections.conclusion ? `
                <div class="card-section">
                    <h3 class="section-title">Conclusion</h3>
                    <p class="section-content">${escapeHtml(sections.conclusion)}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    // Add hover effects
    addCardHoverEffects(card);
    
    return card;
}

// function parseSummaryContent(content) {
//     const sections = {
//         introduction: '',
//         bodyHighlights: '',
//         conclusion: ''
//     };
    
//     // Clean the content first
//     const cleanContent = content;
    
//     // Split content by common patterns
//     const introMatch = cleanContent["introduction"].replace(/\\n/g, '\n').replace(/\\\"/g, '"');
//     const bodyMatch = cleanContent["bodyHighlights"].replace(/\\n/g, '\n').replace(/\\\"/g, '"');
//     const conclusionMatch = cleanContent["conclusion"].replace(/\\n/g, '\n').replace(/\\\"/g, '"');
    
//     if (introMatch) {
//         sections.introduction = introMatch[1].trim();
//     }
    
//     if (bodyMatch) {
//         sections.bodyHighlights = bodyMatch[1].trim();
//     }
    
//     if (conclusionMatch) {
//         sections.conclusion = conclusionMatch[1].trim();
//     }
    
//     // If no structured content found, use the full content as introduction
//     if (!sections.introduction && !sections.bodyHighlights && !sections.conclusion) {
//         sections.introduction = cleanContent;
//     }
    
//     return sections;
// }

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addCardHoverEffects(card) {
    let isHovering = false;
    
    card.addEventListener('mouseenter', function() {
        isHovering = true;
        this.style.transform = 'translateY(-10px) rotateX(5deg) rotateY(5deg)';
        this.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.4)';
    });
    
    card.addEventListener('mouseleave', function() {
        isHovering = false;
        this.style.transform = 'translateY(0) rotateX(0deg) rotateY(0deg)';
        this.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3)';
    });
    
    // Add subtle tilt effect based on mouse position
    card.addEventListener('mousemove', function(e) {
        if (!isHovering) return;
        
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        this.style.transform = `translateY(-10px) rotateX(${5 + rotateX}deg) rotateY(${5 + rotateY}deg)`;
    });
}

function setLoadingState(loading) {
    console.log('Setting loading state:', loading);
    isLoading = loading;
    
    if (loading) {
        // Show loading state
        if (btnText) btnText.style.opacity = '0';
        if (btnLoader) btnLoader.classList.remove('hidden');
        if (findButton) {
            findButton.disabled = true;
            findButton.style.opacity = '0.8';
        }
        if (loadingSection) loadingSection.classList.remove('hidden');
        
        // Add subtle effects to input
        if (topicInput) {
            topicInput.style.pointerEvents = 'none';
            topicInput.style.opacity = '0.7';
        }
    } else {
        // Hide loading state
        if (btnText) btnText.style.opacity = '1';
        if (btnLoader) btnLoader.classList.add('hidden');
        if (findButton) {
            findButton.disabled = false;
            findButton.style.opacity = '1';
        }
        if (loadingSection) loadingSection.classList.add('hidden');
        
        // Restore input
        if (topicInput) {
            topicInput.style.pointerEvents = 'auto';
            topicInput.style.opacity = '1';
        }
    }
}

function showResults() {
    console.log('Showing results');
    if (resultsSection) {
        resultsSection.classList.remove('hidden');
        
        // Smooth scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 300);
    }
}

function hideResults() {
    if (resultsSection) {
        resultsSection.classList.add('hidden');
    }
}

function showError(message) {
    console.log('Showing error:', message);
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }
    
    // Add shake animation to input
    if (topicInput) {
        topicInput.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            topicInput.style.animation = '';
        }, 500);
    }
}

function clearError() {
    if (errorMessage) {
        errorMessage.classList.add('hidden');
        errorMessage.textContent = '';
    }
}

function getErrorMessage(error) {
    if (error.message.includes('Failed to fetch')) {
        return 'Unable to connect to the server. Please check your internet connection and try again.';
    } else if (error.message.includes('HTTP error')) {
        return 'Server error occurred. Please try again later.';
    } else if (error.message.includes('parse')) {
        return 'Error processing the response. Please try again.';
    } else {
        return 'An unexpected error occurred. Please try again.';
    }
}

// Add some interactive background effects
function addInteractiveEffects() {
    const floatingShapes = document.querySelectorAll('.floating-shape');
    console.log('Found floating shapes:', floatingShapes.length);
    
    document.addEventListener('mousemove', function(e) {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        floatingShapes.forEach((shape, index) => {
            const speed = (index + 1) * 2;
            const x = (mouseX - 0.5) * speed;
            const y = (mouseY - 0.5) * speed;
            
            const currentTransform = shape.style.transform || '';
            shape.style.transform = currentTransform + ` translate(${x}px, ${y}px)`;
        });
    });
}

// Debug function to test the input
function testInput() {
    console.log('Testing input field...');
    if (topicInput) {
        topicInput.value = 'test';
        console.log('Input value set to:', topicInput.value);
    }
}

// Make testInput available globally for debugging
window.testInput = testInput;

console.log('App.js loaded successfully');
