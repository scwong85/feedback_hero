let feedbackData = {
    overall_rating: null,
    food_rating: null,
    service_rating: null,
    staff_rating: null,
    cleanliness_rating: null,
    value_rating: null,
    nps_score: null,
    comment: ''
};

let currentQuestion = 0;

function startFeedback() {
    showQuestion(1);
}

function showQuestion(questionNum) {
    document.querySelectorAll('.feedback-card').forEach(card => {
        card.classList.add('hidden');
    });
    
    const questionCard = document.getElementById(`question-${questionNum}`);
    if (questionCard) {
        questionCard.classList.remove('hidden');
        currentQuestion = questionNum;
        
        if (questionNum === 2) {
            initializeStars();
        } else if (questionNum === 3) {
            initializeNPS();
        } else if (questionNum === 4) {
            initializeComment();
        }
    }
}

function selectOverall(rating) {
    feedbackData.overall_rating = rating;
    
    document.querySelectorAll('.emoji-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
    
    setTimeout(() => {
        showQuestion(2);
    }, 300);
}

function initializeStars() {
    const categories = ['food', 'service', 'staff', 'cleanliness', 'value'];
    
    categories.forEach(category => {
        const container = document.querySelector(`.stars[data-category="${category}"]`);
        if (!container) return;
        
        container.innerHTML = '';
        
        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('span');
            star.className = 'star';
            star.textContent = '★';
            star.onclick = () => selectStar(category, i);
            container.appendChild(star);
        }
    });
}

function selectStar(category, rating) {
    feedbackData[`${category}_rating`] = rating;
    
    const stars = document.querySelectorAll(`.stars[data-category="${category}"] .star`);
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

function initializeNPS() {
    const container = document.getElementById('nps-buttons');
    if (!container) return;
    
    container.innerHTML = '';
    
    for (let i = 0; i <= 10; i++) {
        const btn = document.createElement('button');
        btn.className = 'nps-btn';
        btn.textContent = i;
        btn.onclick = () => selectNPS(i);
        container.appendChild(btn);
    }
}

function selectNPS(score) {
    feedbackData.nps_score = score;
    
    document.querySelectorAll('.nps-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
}

function initializeComment() {
    const textarea = document.getElementById('comment');
    const charCount = document.getElementById('char-count');
    
    if (textarea && charCount) {
        textarea.addEventListener('input', function() {
            charCount.textContent = this.value.length;
            feedbackData.comment = this.value;
        });
    }
}

function nextQuestion(questionNum) {
    showQuestion(questionNum);
}

async function submitFeedback() {
    // Validate required field
    if (!feedbackData.overall_rating) {
        alert('Please provide an overall rating');
        return;
    }
    
    document.getElementById('loading').classList.remove('hidden');
    
    console.log('Submitting feedback:', feedbackData); // Debug log
    
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
        });
        
        console.log('Response status:', response.status); // Debug log
        
        const result = await response.json();
        console.log('Response data:', result); // Debug log
        
        document.getElementById('loading').classList.add('hidden');
        
        if (response.ok) {
            document.querySelectorAll('.feedback-card').forEach(card => {
                card.classList.add('hidden');
            });
            document.getElementById('thank-you').classList.remove('hidden');
        } else {
            alert(result.error || 'Something went wrong. Please try again.');
        }
    } catch (error) {
        console.error('Error submitting feedback:', error); // Debug log
        document.getElementById('loading').classList.add('hidden');
        alert('Network error. Please check your connection and try again.');
    }
}
