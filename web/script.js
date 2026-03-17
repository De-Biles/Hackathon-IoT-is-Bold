const SERVER_IP = "100.72.36.107:5000"; // change to your server IP

const WINDOW_SIZE = 20;

let indoorTempBuffer = [];
let indoorRHBuffer = [];
let outdoorTempBuffer = [];
let outdoorRHBuffer = [];

let maxRH = 70;
let minTemp = 15;
let mode = 2; // prioritize 0 - humidity, 1 - temperature, 2 - both
let notify = ""; // url

let lastState = null;

const API_URL = `http://${SERVER_IP}/metrics`;
const HISTORY_API = `http://${SERVER_IP}/history`;
const STATE_URL = `http://${SERVER_IP}/set_state`;
const NOTIFY_URL = `http://${SERVER_IP}/notify`;

function absoluteHumidity(temp, rh){
    temp = Number(temp);
    rh = Number(rh);

    let ah = (6.112 * Math.exp((17.67*temp)/(temp+243.5)) * rh * 2.1674)/(273.15+temp);
    return ah.toFixed(2);
}

function round2(x){
    return Math.round(x * 100) / 100
}

async function loadSettings(){
    try{
        const res = await fetch("http://100.72.36.107:5000/settings");
        const data = await res.json();
        maxRH = Number(data.maxRH);
        minTemp = Number(data.minTemp);
        mode = Number(data.mode);
        notify = data.notify;

        document.getElementById("maxRH").value = maxRH;
        document.getElementById("minTemp").value = minTemp;
        document.getElementById("mode").value = mode;
        document.getElementById("notify").value = notify;
    }catch(e){
        console.log("load settings error", e)
    }
}

async function loadHistory(){
    try{
        const res = await fetch(HISTORY_API)
        const data = await res.json()

        data.forEach(point=>{
            const smoothed = movingAverage(indoorRHBuffer, point.rh)
            addChartPoint(round2(smoothed))
        })

    }catch(e){
        console.log("history load error", e)
    }
}

async function sendNotification(message){
    if (!notify) return;
    try{
        await fetch(NOTIFY_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ 
                message:message,
                topic:notify
            })
        })
    }catch(e){
        console.log("notify error", e)
    }
}

let lastNotifiedState = null;

function handleStateChange(newState, data, diff){
    if(newState !== lastNotifiedState){

        if(newState === "high"){
            sendNotification("🔴 OPEN WINDOW NOW");
        }
        else if(newState === "recommended"){
            sendNotification("🟡 Recommended to open window");
        }
        else if(newState === "okay"){
            sendNotification("🟢 Conditions are good");
        }

        lastNotifiedState = newState
    }

    if(data.i_rh > 80){
        sendNotification("⚠️ Humidity is critical high: " + data.i_rh + "%");
    }

    if(diff > 10){
        sendNotification("💨 Excellent moment to ventilate (AH diff = " + diff.toFixed(2) + ")");
    }
}

function movingAverage(buffer, value){
    buffer.push(value)

    if(buffer.length > WINDOW_SIZE){
        buffer.shift()
    }

    let sum = buffer.reduce((a,b)=>a+b,0)

    return sum / buffer.length
}

function setStateSafe(newState){
    if(newState === lastState) return
    lastState = newState
    sendState(newState)
}

async function sendState(state){
    try{
        await fetch(STATE_URL,{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body: JSON.stringify({state})
        })
    }catch(e){
        console.log("state send error", e)
    }
}

function updateUI(data){
    document.getElementById("indoorTemp").textContent = data.i_temp+" °C"
    document.getElementById("indoorRH").textContent = data.i_rh+" %"
    document.getElementById("outdoorTemp").textContent = data.o_temp+" °C"
    document.getElementById("outdoorRH").textContent = data.o_rh+" %"

    let iAH = absoluteHumidity(data.i_temp, data.i_rh)
    let oAH = absoluteHumidity(data.o_temp, data.o_rh)

    document.getElementById("indoorAH").textContent = iAH+" g/m³"
    document.getElementById("outdoorAH").textContent = oAH+" g/m³"

    let diff = iAH-oAH

    let state = document.getElementById("windowState")

    let condition;
    if (mode == 0) {
        condition = data.i_rh > maxRH;
    } else if (mode == 1) {
        condition = data.i_temp > minTemp && data.o_temp > data.i_temp;
    } else {
        condition = data.i_rh > maxRH || data.i_temp > minTemp && diff > 6;
    }
    console.log("mode", mode, "condition", condition, "diff", diff)

    let newState;

    if (condition && diff > 2 || diff > 6) {
        newState = "high";
        state.textContent = "OPEN WINDOW";
        state.className = "status-high";
    } else if (condition && diff > 2) {
        newState = "recommended";
        state.textContent = "RECOMMENDED TO OPEN WINDOW";
        state.className = "status-recommended";
    } else {
        newState = "okay";
        state.textContent = "KEEP WINDOW CLOSED";
        state.className = "status-okay";
    }


    setStateSafe(newState)
    handleStateChange(newState, data, diff)

    addChartPoint(data.i_rh)
}

async function fetchData(){
    try{
        const res = await fetch(API_URL)
        const d = await res.json()

        const data = {
            i_temp: round2(movingAverage(indoorTempBuffer, d.i_temperature)),
            i_rh: round2(movingAverage(indoorRHBuffer, d.i_humidity)),
            o_temp: round2(movingAverage(outdoorTempBuffer, d.o_temperature)),
            o_rh: round2(movingAverage(outdoorRHBuffer, d.o_humidity))
        }
        updateUI(data)
    }
    catch(err){
        console.error("API error", err)
    }
}

async function saveSettings(){
    maxRH = Number(document.getElementById("maxRH").value);
    minTemp = Number(document.getElementById("minTemp").value);
    mode = Number(document.getElementById("mode").value);
    notify = document.getElementById("notify").value;

    try{
        await fetch("http://100.72.36.107:5000/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ maxRH, minTemp, mode, notify })
        });
        alert("Settings saved!");
    }catch(e){
        console.log("save settings error", e)
        alert("Failed to save settings");
    }
}

const ctx = document.getElementById('humidityChart');

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
        label: 'Indoor RH',
        data: [],
        borderWidth:2
        }]
    },
    options: {
        responsive:true
    }
});

function addChartPoint(value){

    chart.data.labels.push("")
    chart.data.datasets[0].data.push(value)

    if(chart.data.labels.length>500){
        chart.data.labels.shift()
        chart.data.datasets[0].data.shift()
    }

    chart.update()
}

loadSettings();
loadHistory()
fetchData()
setInterval(fetchData,10000)