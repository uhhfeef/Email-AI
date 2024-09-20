// Function to add prediction indicator
async function addPredictionIndicator() {
    observer.disconnect();
    const emailRows = document.querySelectorAll('.zA');
    
    for (const row of emailRows) {
        // chrome.storage.local.remove('recentPredictions', function() {
        //     console.log('Stored predictions cleared');
        // });
        if (!row.querySelector('.prediction')) {
            const predictionSpan = document.createElement('span');
            predictionSpan.className = 'prediction';
            
            fetchRecentPredictions();
            try {
                // call the api here and fetch one by one
                predictionSpan.textContent = '🤔'; // Placeholder
                chrome.storage.local.get(['recentPredictions'], function(result) {

                    const recentPredictions = result.recentPredictions;
                    emailRows.forEach((emailRow, index) => {
                        if (index < recentPredictions.length) {
                            const prediction = recentPredictions[index];
                            const predictionElement = emailRow.querySelector('.prediction');
                            const percentage = (prediction * 100).toFixed(1);
                            predictionElement.textContent = `${percentage}%`;
                            predictionElement.style.fontWeight = 'bold';
                            if (percentage < 50) {
                                predictionElement.style.color = 'red';
                            } else {
                                predictionElement.style.color = 'green';
                            }
                        }
                    });
                })
            } catch (error) {
                console.error('Error getting message ID:', error);
                predictionSpan.textContent = '❓'; // Error indicator
            }
            
            const dateElement = row.querySelector('.xW');
            predictionSpan.style.marginRight = '0.5em';
            dateElement.insertBefore(predictionSpan, dateElement.firstChild);
        }
    }
    
    observer.observe(document.body, { childList: true, subtree: true });
}

const observer = new MutationObserver(addPredictionIndicator);
observer.observe(document.body, { childList: true, subtree: true });

function fetchRecentPredictions() {
    fetch('http://localhost:5002/get-recent-predictions')
    .then(response => response.json())
    .then(predictions => {
      // Store predictions in extension's local storage
      chrome.storage.local.set({recentPredictions: predictions}, function() {
        console.log('Predictions stored');
      });
    })
    .catch(error => console.error('Error:', error));
}