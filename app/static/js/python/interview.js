const preview = document.getElementById("preview");
const videoContainer = document.getElementById("videoContainer");
const chatBox = document.getElementById("chat-box");
const form = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const transcriptBox = document.getElementById("transcriptBox");
const autoSendToggle = document.getElementById("autoSendToggle");
const startVoiceBtn = document.getElementById("startVoiceBtn");
// Extract conversation_id from URL
const urlParams = new URLSearchParams(window.location.search);
const conversationId = urlParams.get("conversation_id");
let avatarMuted = false;

  document.getElementById('muteToggleBtn').addEventListener('click', function () {
    avatarMuted = !avatarMuted;
    this.textContent = avatarMuted ? '🔈 Unmute Avatar Auto Speak' : '🔇 Mute Avatar Auto Speak';
       
  });

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
    const url = `/python/ask/interview?conversation_id=${encodeURIComponent(conversationId)}`;
    $.post(url, { message: msg }, function(data) {
        appendMessage("bot", data.response);
    });
    }
});



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
<title>Professor Python</title>
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
<h1 style="text-align:center;">Professor Python</h1>
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
            const url = `/python/ask/interview?conversation_id=${encodeURIComponent(conversationId)}`;
            $.post(url, { message: finalTranscript.trim() }, function(data) {
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






// Add this to make the avatar "speak" by animating it and optionally playing speech
function speakAvatar(text) {
    if (avatarMuted) return;

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

// Enable Bootstrap tooltips on all elements with [data-bs-toggle="tooltip"]
document.addEventListener("DOMContentLoaded", function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});




// For code editor
document.getElementById('showEditorBtn').addEventListener('click', function () {
const modal = new bootstrap.Modal(document.getElementById('codeEditorModal'));
modal.show();
});
// For CodeMirror
let editor;
  document.addEventListener("DOMContentLoaded", function () {
    editor = CodeMirror.fromTextArea(document.getElementById("pythonCode"), {
      mode: { name: "python", version: 3, singleLineStringErrors: false },
      theme: "material",
      lineNumbers: true,
      lineWrapping: true,
      indentUnit: 4,
      tabSize: 4,
    });

    // Optional: refresh CodeMirror in case it's in a hidden modal
    setTimeout(() => editor.refresh(), 100);
  });

let pyodideReady = false;
let pyodide = null;

async function loadPyodideAndPackages() {
  pyodide = await loadPyodide();
  pyodideReady = true;
}

loadPyodideAndPackages();

document.getElementById("runPythonBtn").addEventListener("click", async () => {
  const code = editor.getValue(); //document.getElementById("pythonCode").value;
  const outputElement = document.getElementById("pythonOutput");

  if (!pyodideReady) {
    outputElement.textContent = "Pyodide is still loading...";
    return;
  }

  try {
    let output = [];
    let error = [];

    // Capture stdout and stderr
    pyodide.setStdout({
      batched: (msg) => output.push(msg)
    });
    pyodide.setStderr({
      batched: (msg) => error.push(msg)
    });

    await pyodide.runPythonAsync(code);

    if (error.length > 0) {
      outputElement.textContent = `❌ Error:\n${error.join("")}`;
    } else {
      outputElement.textContent = output.join("") || "✓ Code executed";
    }
  } catch (err) {
    outputElement.textContent = `❌ Exception:\n${err}`;
  }
});


// Copy code
document.getElementById("copyCodeBtn").addEventListener("click", function () {
    const code = editor.getValue();
    navigator.clipboard.writeText(code).then(() => {
    this.innerText = "✅ Copied!";
    setTimeout(() => this.innerText = "📋 Copy", 2000);
    }).catch(err => {
    console.error('Copy failed', err);
    alert("Copy failed. Please try manually.");
    });
});

let tabChangeCount = 0;

document.addEventListener("visibilitychange", function () {
if (document.hidden) {
    tabChangeCount++;

    // Show popup warning
    alert(`⚠️ Warning! You have changed window ${tabChangeCount} time${tabChangeCount > 1 ? 's' : ''}! Do not change window at the time of interview.`);
}
});


function stopCamera() {
  if (window.combinedStream) {
    window.combinedStream.getTracks().forEach(track => {
      track.stop(); // Stops both video and audio tracks
    });
    // Clear the video preview
    const preview = document.getElementById('preview');
    preview.srcObject = null;

    // Optional cleanup
    window.combinedStream = null;
  }
}


let videoVisible = true;

document.getElementById("toggleVideoBtn").addEventListener("click", function () {
const videoContainer = document.getElementById("videoContainer");

if (videoVisible) {
    stopCamera();
    videoContainer.style.display = "none";
    this.innerText = "🎥 Show Video";
    this.classList.remove("btn-outline-danger");
    this.classList.add("btn-outline-success");
} else {
    startCamera();
    videoContainer.style.display = "block";
    this.innerText = "🎥 Hide Video";
    this.classList.remove("btn-outline-success");
    this.classList.add("btn-outline-danger");
}

videoVisible = !videoVisible;
});
