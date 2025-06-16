document.addEventListener("DOMContentLoaded", function() {
    // Use the remaining time from server or default 5 mins
    let timeLeft = typeof remainingTimeFromServer !== 'undefined' ? remainingTimeFromServer : 5 * 60; // seconds

    const timerDisplay = document.getElementById("timer");

    const timerInterval = setInterval(function() {
        let minutes = Math.floor(timeLeft / 60);
        let seconds = timeLeft % 60;
        timerDisplay.textContent = `Time Left: ${minutes}:${seconds < 5 ? '0' : ''}${seconds}`;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            alert("Time's up! Submitting your test.");
            submitAnswers();
        }
        timeLeft--;
        // Save remaining time to session every tick (or every few seconds for optimization)
        // if (timeLeft % 120 === 0) { // every 120 seconds
        //     saveProgress();
        // }
    }, 1000);

    // Start from the saved current question index or 0
    let currentQuestion = typeof currentQuestionIndex !== 'undefined' ? currentQuestionIndex : 0;

    const questions = document.querySelectorAll(".question-block");
    questions.forEach(q => q.style.display = "none");
    questions[currentQuestion].style.display = "block";

    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    function updateButtons() {
        prevBtn.disabled = currentQuestion === 0;
        nextBtn.disabled = currentQuestion === questions.length - 1;
    }

    updateButtons();

    nextBtn.addEventListener("click", function() {
        questions[currentQuestion].style.display = "none";
        currentQuestion = Math.min(currentQuestion + 1, questions.length - 1);
        questions[currentQuestion].style.display = "block";
        updateButtons();
        // saveProgress();
    });

    prevBtn.addEventListener("click", function() {
        questions[currentQuestion].style.display = "none";
        currentQuestion = Math.max(currentQuestion - 1, 0);
        questions[currentQuestion].style.display = "block";
        updateButtons();
        saveProgress();
    });

    document.getElementById("mockTestForm").addEventListener("submit", function(e) {
        e.preventDefault();
        submitAnswers();
    });

    // Preselect saved answers if any
    if (typeof savedAnswers !== 'undefined' && savedAnswers) {
        for (const [questionName, selectedValue] of Object.entries(savedAnswers)) {
            const radios = document.getElementsByName(questionName);
            radios.forEach(radio => {
                if (radio.value === selectedValue) {
                    radio.checked = true;
                }
            });
        }
    }

    function saveProgress() {
        // Collect current answers
        const formData = new FormData(document.getElementById("mockTestForm"));
        const answers = {};
        formData.forEach((value, key) => {
            answers[key] = value;
        });

        fetch('/mocktest/save_progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_question_index: currentQuestion,
                remaining_time: timeLeft,
                answers: answers
            })
        }).catch(err => {
            console.error('Error saving progress:', err);
        });
    }

    function submitAnswers() {
        const formData = new FormData(document.getElementById("mockTestForm"));
        const answers = {};
        formData.forEach((value, key) => {
            answers[key] = value;
        });

        fetch(window.location.origin + '/mocktest/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                answers: answers,
                topic: window.location.pathname.split('/').pop()
            })
        })
        .then(response => response.json())
        .then(data => {
            // Clear saved session progress on submit
            fetch('/mocktest/save_progress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_question_index: 0,
                    remaining_time: 5 * 60,
                    answers: {}
                })
            });
            window.location.href = `/mocktest/result`;
        })
        .catch(error => console.error('Error:', error));
    }
});
