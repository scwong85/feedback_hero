// Set current date
const dateElement = document.getElementById('current-date');
if (dateElement) {
    dateElement.textContent = new Date().toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

let chart = null;

async function loadDashboardData() {
    try {
        console.log('Loading dashboard data...'); // Debug log
        const response = await fetch('/dashboard/api/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Dashboard data received:', data); // Debug log
        
        // Update stats
        document.getElementById('today-count').textContent = data.today.count;
        document.getElementById('today-avg').textContent = data.today.avg_rating.toFixed(1);
        
        document.getElementById('week-count').textContent = data.week.count;
        document.getElementById('week-avg').textContent = data.week.avg_rating.toFixed(1);
        
        document.getElementById('nps-score').textContent = data.nps;
        const npsLabel = document.getElementById('nps-label');
        if (data.nps > 50) {
            npsLabel.textContent = 'Excellent';
            npsLabel.style.color = '#10b981';
        } else if (data.nps > 0) {
            npsLabel.textContent = 'Good';
            npsLabel.style.color = '#f59e0b';
        } else {
            npsLabel.textContent = 'Needs Improvement';
            npsLabel.style.color = '#ef4444';
        }
        
        document.getElementById('total-count').textContent = data.total_responses;
        
        // Update categories
        const categories = ['food', 'service', 'staff', 'cleanliness', 'value'];
        categories.forEach(cat => {
            const rating = data.categories[cat];
            const ratingElement = document.getElementById(`cat-${cat}`);
            if (ratingElement) {
                ratingElement.textContent = rating.toFixed(1);
            }
            
            const starsContainer = document.getElementById(`stars-${cat}`);
            if (starsContainer) {
                const fullStars = Math.floor(rating);
                const hasHalf = rating % 1 >= 0.5;
                let starsHTML = '';
                
                for (let i = 0; i < fullStars; i++) {
                    starsHTML += '★';
                }
                if (hasHalf && fullStars < 5) {
                    starsHTML += '☆';
                }
                
                starsContainer.textContent = starsHTML;
            }
        });
        
        // Create chart
        createWeekChart(data.daily_chart);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        alert('Error loading dashboard data. Check console for details.');
    }
}

function createWeekChart(dailyData) {
    const ctx = document.getElementById('weekChart');
    if (!ctx) return;
    
    if (chart) {
        chart.destroy();
    }
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(d => d.date),
            datasets: [{
                label: 'Feedback Count',
                data: dailyData.map(d => d.count),
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

async function loadFeedbackList(page = 1) {
    try {
        console.log(`Loading feedback list page ${page}...`); // Debug log
        const response = await fetch(`/dashboard/api/feedback?page=${page}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Feedback list received:', data); // Debug log
        
        const tbody = document.getElementById('feedback-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (data.feedback.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="loading-cell">No feedback yet</td></tr>';
            return;
        }
        
        data.feedback.forEach(f => {
            const row = document.createElement('tr');
            
            const date = new Date(f.timestamp);
            const ratingClass = f.overall_rating === 3 ? 'rating-high' : 
                               f.overall_rating === 2 ? 'rating-mid' : 'rating-low';
            
            const emojiMap = {1: '😞', 2: '😐', 3: '😊'};
            
            row.innerHTML = `
                <td>${date.toLocaleDateString()}<br><small>${date.toLocaleTimeString()}</small></td>
                <td><span class="rating-badge ${ratingClass}">${emojiMap[f.overall_rating]}</span></td>
                <td>${f.food_rating || '-'}</td>
                <td>${f.service_rating || '-'}</td>
                <td>${f.staff_rating || '-'}</td>
                <td>${f.cleanliness_rating || '-'}</td>
                <td>${f.value_rating || '-'}</td>
                <td>${f.nps_score !== null ? f.nps_score : '-'}</td>
                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${f.comment || '-'}
                </td>
                <td>
                    <button class="review-btn ${f.reviewed ? 'reviewed' : ''}" 
                            onclick="toggleReviewed(${f.id})">
                        ${f.reviewed ? '✓ Reviewed' : 'Mark Reviewed'}
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        // Update pagination
        createPagination(data.current_page, data.pages);
        
    } catch (error) {
        console.error('Error loading feedback:', error);
        const tbody = document.getElementById('feedback-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="10" class="loading-cell">Error loading feedback. Check console.</td></tr>';
        }
    }
}

function createPagination(current, total) {
    const pagination = document.getElementById('pagination');
    if (!pagination || total <= 1) return;
    
    pagination.innerHTML = '';
    
    for (let i = 1; i <= total; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === current ? 'active' : '';
        btn.onclick = () => loadFeedbackList(i);
        pagination.appendChild(btn);
    }
}

async function toggleReviewed(feedbackId) {
    try {
        const response = await fetch(`/dashboard/api/feedback/${feedbackId}/review`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadFeedbackList();
        }
    } catch (error) {
        console.error('Error toggling review status:', error);
    }
}
