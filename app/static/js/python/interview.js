const preview = document.getElementById("preview");
const videoContainer = document.getElementById("videoContainer");
const chatBox = document.getElementById("chat-box");
const form = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const transcriptBox = document.getElementById("transcriptBox");
const autoSendToggle = document.getElementById("autoSendToggle");
const startVoiceBtn = document.getElementById("startVoiceBtn");

// async function startCamera() {
//     try {
//     const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
//     preview.srcObject = stream;
//     } catch (err) {
//     alert("Could not access camera/mic: " + err.message);
//     console.error(err);
//     }
// }
async function startCamera() {
  try {
    // Fetch video stream
    const videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
    // Fetch mic stream if the device is not mobile
    const isMobile = /Mobi|Android/i.test(navigator.userAgent);
    console.log(isMobile)
    let combinedStream = null;
    if (!isMobile) {
        const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Combine video and audio
            combinedStream = new MediaStream([
            ...videoStream.getVideoTracks(),
              ...audioStream.getAudioTracks()
            ]);
    } else {
        // Only video
        combinedStream = new MediaStream([
        ...videoStream.getVideoTracks(),
        ]);
    }
    

    // Assign to preview
    preview.srcObject = combinedStream;

    // Save for later use
    window.combinedStream = combinedStream;

  } catch (err) {
    alert("Could not access camera/mic: " + err.message);
    console.error(err);
  }
}

startCamera();

// DRAG FUNCTIONALITY
let offsetX, offsetY, isDragging = false;

videoContainer.addEventListener('mousedown', function(e) {
    isDragging = true;
    offsetX = e.clientX - videoContainer.offsetLeft;
    offsetY = e.clientY - videoContainer.offsetTop;
    videoContainer.style.cursor = "grabbing";
});

document.addEventListener('mousemove', function(e) {
    if (isDragging) {
    videoContainer.style.left = (e.clientX - offsetX) + 'px';
    videoContainer.style.top = (e.clientY - offsetY) + 'px';
    }
});

document.addEventListener('mouseup', function() {
    isDragging = false;
    videoContainer.style.cursor = "grab";
});

videoContainer.addEventListener('touchstart', function(e) {
    const touch = e.touches[0];
    offsetX = touch.clientX - videoContainer.offsetLeft;
    offsetY = touch.clientY - videoContainer.offsetTop;
});

videoContainer.addEventListener('touchmove', function(e) {
    e.preventDefault();
    const touch = e.touches[0];
    videoContainer.style.left = (touch.clientX - offsetX) + 'px';
    videoContainer.style.top = (touch.clientY - offsetY) + 'px';
}, { passive: false });

// Chat Logic
form.addEventListener("submit", function(e) {
    e.preventDefault();
    const msg = messageInput.value.trim();
    if (msg) {
    appendMessage("user", msg);
    messageInput.value = "";
    $.post("/python/ask/interview", { message: msg }, function(data) {
        appendMessage("bot", data.response);
    });
    }
});

// form.addEventListener("submit", function(e) {
//     e.preventDefault();
//     const msg = messageInput.value.trim();
//     if (msg) {
//         appendMessage("user", msg);
//         messageInput.value = "";
        
//         $.ajax({
//             type: "POST",
//             url: "/ask",
//             data: { message: msg },
//             success: function(data) {
//                 appendMessage("bot", data.response);
//             },
//             error: function(xhr) {
//                 if (xhr.status === 429) {
//                     // Server responded with 429 Too Many Requests
//                     let errorMessage = "⛔ Too many requests. Please wait before trying again.";
//                     try {
//                         let json = JSON.parse(xhr.responseText);
//                         if (json.message) {
//                             errorMessage = json.message;
//                         }
//                     } catch (e) {
//                         // Not JSON, fallback to default
//                     }
//                     // Show popup alert
//                     alert(errorMessage);
//                 } else {
//                     alert("An error occurred while processing your request.");
//                 }
//             }
//         });
//     }
// });


function appendMessage(sender, text) {
    const div = document.createElement("div");
    div.className = sender === "user" ? "user-message" : "bot-message";
    div.innerHTML = sender === "bot" ? `<button class="speak-btn" onclick="speakText(this)">🔊</button>${text}`: text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (sender === "bot") {
        speakAvatar(text);
    }
}


// Download chat
document.getElementById("download-btn").addEventListener("click", function () {
    const chatContent = document.getElementById("chat-box").innerHTML;
    const now = new Date();
    const timestamp = now.toISOString().slice(0, 19).replace(/[:T]/g, "-");
    const filename = `chat_${timestamp}.html`;
    const html = `
<!DOCTYPE html>
<html>
<head>
<title>Python Mock Interview</title>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { padding: 10px; font-family: Arial; }
#chat-box { width: 100%; min-height: 100vh; background: #f9f9f9; padding: 15px; box-sizing: border-box; }
.user-message { background: #d4edda; color: #155724; padding: 10px; margin: 5px 0; text-align: right; border-radius: 8px; }
.bot-message { background: #e0e0e0; color: #303235; padding: 10px; margin: 5px 0; text-align: left; border-radius: 8px; }
</style>
</head>
<body>
<h1 style="text-align:center;">Python Mock Interview</h1>
<div id="chat-box">
${chatContent}
</div>
<script>
// Add this so the 🔊 button next to bot message will trigger speech
function speakText(button) {
const nextElem = button.nextElementSibling;
if (!nextElem) {
console.warn('No next element sibling found!');
return;
}

let textToSpeak = nextElem.textContent || '';

// Remove emojis (your regex)
textToSpeak = textToSpeak.replace(/([\\u2700-\\u27BF]|[\\uE000-\\uF8FF]|\\uD83C[\\uDC00-\\uDFFF]|\\uD83D[\\uDC00-\\uDFFF]|\\uD83E[\\uDD00-\\uDDFF])/g, '');

textToSpeak = textToSpeak.trim();

console.log("textToSpeak: ", textToSpeak);

if(textToSpeak) {
const utterance = new SpeechSynthesisUtterance(textToSpeak);
speechSynthesis.speak(utterance);
} else {
console.warn('Nothing to speak!');
}
}

<\/script>
</body>
</html>`;
    const blob = new Blob([html], { type: "text/html" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
});

// Speech Recognition

let recognition;
let isRecognizing = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    let isMobile_detected = /Mobi|Android/i.test(navigator.userAgent);

    let finalTranscript = '';

    recognition.onresult = (event) => {
        let interimTranscript = '';
        if (isMobile_detected) {
            finalTranscript = '';  // reset on mobile devices
        }

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        transcriptBox.innerHTML = `🎤 <strong>Live Transcription:</strong> <em>${finalTranscript} ${interimTranscript}</em>`;
    };

    recognition.onerror = (e) => {
        console.error("Speech Recognition Error:", e.error);
    };

    recognition.onend = () => {
        isRecognizing = false;
        startVoiceBtn.textContent = "🎙 Start Voice Input";
        transcriptBox.innerHTML += " (Stopped)";

        // Send final transcript if auto-send is enabled
        if (autoSendToggle.checked && finalTranscript.trim()) {
            appendMessage("user", finalTranscript.trim());
            $.post("/python/ask/interview", { message: finalTranscript.trim() }, function(data) {
                appendMessage("bot", data.response);
            });
            finalTranscript = '';  // reset for next session
        }
    };

    startVoiceBtn.onclick = () => {
        if (isRecognizing) {
            recognition.stop();
        } else {
            finalTranscript = '';
            recognition.start();
            isRecognizing = true;
            transcriptBox.innerHTML = "🎤 <strong>Live Transcription:</strong> <em>Listening...</em>";
            startVoiceBtn.textContent = "⏹ Stop Voice Input";
        }
    };
} else {
    transcriptBox.innerHTML = "🎤 Speech recognition not supported in this browser.";
    startVoiceBtn.disabled = true;
}

// let recognition;
// let isRecognizing = false;

// if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
//     const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
//     recognition = new SpeechRecognition();
//     recognition.continuous = true;
//     recognition.interimResults = true;
//     recognition.lang = 'en-US';
//     let isMobile_detected = /Mobi|Android/i.test(navigator.userAgent);

//     let finalTranscript = '';

//     recognition.onresult = (event) => {
//     let interimTranscript = '';
//     if(isMobile_detected){
//         finalTranscript = '';
//     }
//     for (let i = event.resultIndex; i < event.results.length; ++i) {
//         const transcript = event.results[i][0].transcript;
//         if (event.results[i].isFinal) {
//             finalTranscript += transcript;
//         } else {
//         interimTranscript += transcript;
//         }
//     }
//     transcriptBox.innerHTML = `🎤 <strong>Live Transcription:</strong> <em>${finalTranscript} ${interimTranscript}</em>`;
//     if (autoSendToggle.checked && finalTranscript .trim()) {
//         appendMessage("user", finalTranscript );
//         $.post("/ask", { message: finalTranscript }, function(data) {
//         appendMessage("bot", data.response);
//         });
//         finalTranscript = '';
//     }
//     };

//     recognition.onerror = (e) => {
//     console.error("Speech Recognition Error:", e.error);
//     };

//     recognition.onend = () => {
//     isRecognizing = false;
//     startVoiceBtn.textContent = "🎙 Start Voice Input";
//     transcriptBox.innerHTML += " (Stopped)";
//     };

//     startVoiceBtn.onclick = () => {
//     if (isRecognizing) {
//         recognition.stop();
//     } else {
//         finalTranscript = '';
//         recognition.start();
//         isRecognizing = true;
//         transcriptBox.innerHTML = "🎤 <strong>Live Transcription:</strong> <em>Listening...</em>";
//         startVoiceBtn.textContent = "⏹ Stop Voice Input";
//     }
//     };
// } else {
//     transcriptBox.innerHTML = "🎤 Speech recognition not supported in this browser.";
//     startVoiceBtn.disabled = true;
// }


// === Speech Recognition Setup ===
// let recognition;
// let isRecognizing = false;
// let finalTranscript = '';

// if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
//     const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
//     recognition = new SpeechRecognition();
//     recognition.continuous = true;
//     recognition.interimResults = true;
//     recognition.lang = 'en-US';

//     recognition.onresult = (event) => {
//         let interimTranscript = '';
//         finalTranscript = '';
//         for (let i = event.resultIndex; i < event.results.length; ++i) {
//             const transcript = event.results[i][0].transcript;
//             if (event.results[i].isFinal) {
//                 finalTranscript += transcript + ' ';
//             } else {
//                 interimTranscript += transcript;
//             }
//         }

//         // Update transcript display
//         const transcriptBox = document.getElementById('transcriptBox');
//         transcriptBox.innerHTML = `🎤 <strong>Live Transcription:</strong> <em>${finalTranscript} ${interimTranscript}</em>`;

//         // Auto-send feature
//         const autoSendToggle = document.getElementById('autoSendToggle');
//         if (autoSendToggle.checked && finalTranscript.trim()) {
//             appendMessage("user", finalTranscript.trim());
//             $.post("/ask", { message: finalTranscript.trim() }, function(data) {
//                 appendMessage("bot", data.response);
//             });
//             finalTranscript = '';
//         }
//     };

//     recognition.onerror = (e) => {
//         console.error("Speech Recognition Error:", e.error);
//         const transcriptBox = document.getElementById('transcriptBox');
//         transcriptBox.innerHTML += ` <span style="color:red;">(Error: ${e.error})</span>`;
//     };

//     recognition.onend = () => {
//         isRecognizing = false;
//         document.getElementById('startVoiceBtn').textContent = "🎙 Start Voice Input";
//         const transcriptBox = document.getElementById('transcriptBox');
//         transcriptBox.innerHTML += " (Stopped)";
//     };

//     document.getElementById('startVoiceBtn').addEventListener('click', () => {
//         const transcriptBox = document.getElementById('transcriptBox');
//         if (isRecognizing) {
//             recognition.stop();
//         } else {
//             finalTranscript = '';
//             recognition.start();
//             isRecognizing = true;
//             transcriptBox.innerHTML = "🎤 <strong>Live Transcription:</strong> <em>Listening...</em>";
//             document.getElementById('startVoiceBtn').textContent = "⏹ Stop Voice Input";
//         }
//     });
// } else {
//     const transcriptBox = document.getElementById('transcriptBox');
//     transcriptBox.innerHTML = "🎤 Speech recognition not supported in this browser.";
//     document.getElementById('startVoiceBtn').disabled = true;
// }









// Add this to make the avatar "speak" by animating it and optionally playing speech
function speakAvatar(text) {
    const avatar = document.getElementById("avatar");
    avatar.classList.add("speaking");

    // Use SpeechSynthesis to speak text aloud
    let textToSpeak = text.replace(/<[^>]*>/g, '');
    textToSpeak = textToSpeak.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|\uD83E[\uDD00-\uDDFF])/g, '');

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.onend = () => {
        avatar.classList.remove("speaking");
    };
    speechSynthesis.speak(utterance);
}


function speakText(button) {
    const nextElem = button.nextElementSibling;
    if (!nextElem) {
    console.warn('No next element sibling found!');
    return;
    }

    let textToSpeak = nextElem.textContent || '';

    // Remove emojis (your regex)
    textToSpeak = textToSpeak.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|\uD83E[\uDD00-\uDDFF])/g, '');

    textToSpeak = textToSpeak.trim();

    if(textToSpeak) {
        avatar.classList.add("speaking");
        // Use SpeechSynthesis to speak text aloud
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.onend = () => {
            avatar.classList.remove("speaking");
        };
        speechSynthesis.speak(utterance);
    } else {
        console.warn('Nothing to speak!');
    }
}


let mediaRecorder;
let recordedChunks = [];

document.getElementById("downloadVideoBtn").addEventListener("click", function () {
if (!preview.srcObject) {
    alert("Camera not started!");
    return;
}

if (!mediaRecorder || mediaRecorder.state === "inactive") {
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(preview.srcObject);

    mediaRecorder.ondataavailable = function (e) {
        if (e.data.size > 0) {
            recordedChunks.push(e.data);
        }
    };

    mediaRecorder.onstop = function () {
        const blob = new Blob(recordedChunks, { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = `video_${new Date().toISOString().replace(/[:.]/g, '-')}.webm`;
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
    };

    mediaRecorder.start();
    alert("Recording started! Click again to stop and download.");
    document.getElementById("downloadVideoBtn").innerText = "Stop Video Record";
} else if (mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        alert("Recording stopped. Video will download now.");
        document.getElementById("downloadVideoBtn").innerText = "Record Video";

    }
});


document.getElementById("downloadScreenBtn").addEventListener("click", async () => {
    try {
        // Get full screen with system audio (user must select "Entire Screen" and enable audio)
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                displaySurface: "monitor" // Suggest full screen
            },
            audio: true // Only works on Chrome + Windows/Linux for system audio
        });

        // Get microphone audio
        const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // AudioContext to mix audio sources
        const audioContext = new AudioContext();
        const destination = audioContext.createMediaStreamDestination();

        const screenAudio = audioContext.createMediaStreamSource(screenStream);
        const micAudio = audioContext.createMediaStreamSource(micStream);

        screenAudio.connect(destination);
        micAudio.connect(destination);

        // Combine video from screen + mixed audio
        const combinedStream = new MediaStream([
            ...screenStream.getVideoTracks(),
            ...destination.stream.getAudioTracks()
        ]);

        const recorder = new MediaRecorder(combinedStream);
        const chunks = [];

        recorder.ondataavailable = (event) => {
            if (event.data.size > 0) chunks.push(event.data);
        };

        recorder.onstop = () => {
            const blob = new Blob(chunks, { type: "video/webm" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `full_screen_with_audio_${new Date().toISOString().replace(/[:.]/g, "-")}.webm`;
            a.click();
            URL.revokeObjectURL(url);
        };

        recorder.start();
        alert("Recording started. Stop screen sharing to end.");
        document.getElementById("downloadScreenBtn").disabled = true;
        // Stop when screen sharing ends
        screenStream.getVideoTracks()[0].addEventListener("ended", () => {
            recorder.stop();
            document.getElementById("downloadScreenBtn").disabled = false;
        });

    } catch (err) {
        console.error("Screen recording error:", err);
        alert("Failed to start screen recording: " + err.message);
    }
});

// Making Chat widow show/hide
let chatBoxVisible = true;
document.getElementById('chatShowHideBtn').addEventListener("click", async () =>{
    try{
        const chatWindow = document.getElementById('chat-box');
        const chatShowHideBtn = document.getElementById('chatShowHideBtn');
        if (chatBoxVisible){
            chatBox.style.visibility = 'hidden';
            chatShowHideBtn.textContent = '👁️ Show Chat';
        }else{
            chatBox.style.visibility = 'visible';
            chatShowHideBtn.textContent = '🙈 Hide Chat';

        }
        chatBoxVisible = !chatBoxVisible; // toggle state

    } catch(err){
        console.error("Chat window show/hide error:", err);
        alert("Failed to show/hide chat window: " + err.message);
    }
});


// DRAG FUNCTIONALITY FOR AVATAR
const avatar = document.getElementById('avatar');
let avatarOffsetX, avatarOffsetY, isAvatarDragging = false;

avatar.addEventListener('mousedown', function(e) {
isAvatarDragging = true;
avatarOffsetX = e.clientX - avatar.offsetLeft;
avatarOffsetY = e.clientY - avatar.offsetTop;
avatar.style.cursor = "grabbing";
});

document.addEventListener('mousemove', function(e) {
if (isAvatarDragging) {
avatar.style.left = (e.clientX - avatarOffsetX) + 'px';
avatar.style.top = (e.clientY - avatarOffsetY) + 'px';
}
});

document.addEventListener('mouseup', function() {
isAvatarDragging = false;
avatar.style.cursor = "grab";
});

// Touch support for avatar
avatar.addEventListener('touchstart', function(e) {
const touch = e.touches[0];
avatarOffsetX = touch.clientX - avatar.offsetLeft;
avatarOffsetY = touch.clientY - avatar.offsetTop;
});

avatar.addEventListener('touchmove', function(e) {
e.preventDefault();
const touch = e.touches[0];
avatar.style.left = (touch.clientX - avatarOffsetX) + 'px';
avatar.style.top = (touch.clientY - avatarOffsetY) + 'px';
}, { passive: false });

// Simple mobile device detection

function isMobile() {
    return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

document.addEventListener("DOMContentLoaded", function() {
    if (isMobile()) {
    const videoBtn = document.getElementById('downloadVideoBtn');
    const screenBtn = document.getElementById('downloadScreenBtn');
    if (videoBtn) {
        videoBtn.disabled = true;
        videoBtn.title = "Video recording is not supported on mobile devices.";
    }
    if (screenBtn) {
        screenBtn.disabled = true;
        screenBtn.title = "Screen recording is not supported on mobile devices.";
    }
    }
});

