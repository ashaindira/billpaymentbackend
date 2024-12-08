const billForm = document.getElementById('bill-form');
const billsList = document.getElementById('bills');
const startRecordingButton = document.getElementById('start-recording');
const recordingStatus = document.getElementById('recording-status');

billForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const billName = document.getElementById('bill-name').value;
    const dueDate = document.getElementById('due-date').value;
    const category = document.getElementById('category').value;

    // Send data to the server
    fetch('/add-bill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ billName, dueDate, category })
    }).then(response => response.json())
      .then(data => {
        addBillToUI(data);
        billForm.reset();
    });
});

function addBillToUI(bill) {
    const li = document.createElement('li');
    li.innerHTML = `
        ${bill.name} - ${bill.dueDate} (${bill.category})
        <button onclick="deleteBill(${bill.id})">Delete</button>
    `;
    billsList.appendChild(li);
}

startRecordingButton.addEventListener('click', () => {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        recordingStatus.textContent = 'Listening...';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        recordingStatus.textContent = `You said: ${transcript}`;
    };

    recognition.start();
});
