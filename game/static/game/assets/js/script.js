var socket;
let redPlayer = false;
let yellowPlayer = false;
let winner = false;
let roomName = "";

document.addEventListener('DOMContentLoaded', function () {
    var fireworks = document.getElementsByClassName("pyro")[0];
    fireworks.style.display = "none";

    socket = new WebSocket('ws://sconfour.herokuapp.com/ws/game/');
    socket.onopen = function() {

    };

    socket.onmessage = function(event){
        var data = JSON.parse(event.data);
        
        if (data.command == "update"){
            serverBoard = JSON.parse(data.data);
            console.log(serverBoard);
            generateBoardHTML(serverBoard);



        }else if (data.command == "joinRoom"){
            roomName = data.data
            sJoinRoom();



        }else if (data.command == "assignColor"){
            if(data.data == "red"){
                redPlayer = true;
            }else if(data.data == "yellow"){
                yellowPlayer = true;
            }
            document.getElementById("currentColor").innerHTML = `Current Color: ${data.data}`


        }else if(data.command == "initialUpdate"){
            serverBoard = JSON.parse(JSON.parse(data.data));
            console.log(serverBoard);
            generateBoardHTML(serverBoard);


        }else if(data.command == "gameWon"){
            console.log(data.data);
            var fireworks = document.getElementsByClassName("pyro")[0];
            fireworks.style.display = "block";
            winner = true;


        }else if(data.command == "resetBoard"){
            var fireworks = document.getElementsByClassName("pyro")[0];
            fireworks.style.display = "none";
            winner = false;
        
        
        }else if(data.command == "roomError"){
            var roomNameInput = document.getElementById("roomName");
            var joinRoomButton = document.getElementById("joinRoomButton");
            var createRoomButton = document.getElementById("createRoomButton");
            document.getElementById("currentRoom").innerHTML = "";
            createRoomButton.disabled = false;
            joinRoomButton.disabled = false;
            roomNameInput.disabled = false;
            roomNameInput.value = "";
            roomNameInput.placeholder = data.data;
        }


    }

});

function sCreateRoom(newRoomName){
    socket.send(JSON.stringify({
        'command': 'createRoom',
        'roomName': newRoomName
    }));
}

function sJoinRoom(){
    socket.send(JSON.stringify({
        'command': 'joinRoom',
        'roomName': roomName
    }));
    document.getElementById("currentRoom").innerHTML = `Current Room: ${roomName}`;
}

function sUpdate(){
    socket.send(JSON.stringify({
        'command': 'update',
        'roomName': roomName,
        'redPlayer': redPlayer,
        'yellowPlayer': yellowPlayer
    }));
}

function sColumnClicked(colNum){
    socket.send(JSON.stringify({
        'command': 'columnClicked',
        'roomName': roomName,
        'redPlayer': redPlayer,
        'yellowPlayer': yellowPlayer,
        'colNum': colNum
    }));
}

function sResetBoard(){
    socket.send(JSON.stringify({
        'command': 'resetBoard',
        'roomName': roomName
    }));
}

function joinRoom(){
    var roomNameInput = document.getElementById("roomName");
    var newRoomName = roomNameInput.value;
    var joinRoomButton = document.getElementById("joinRoomButton");
    var createRoomButton = document.getElementById("createRoomButton");
    if(newRoomName){
        createRoomButton.disabled = true;
        joinRoomButton.disabled = true;
        roomNameInput.disabled = true;
        roomName = newRoomName;
        sJoinRoom();
    }
}

function createRoom(){
    var roomNameInput = document.getElementById("roomName");
    var newRoomName = roomNameInput.value;
    var createRoomButton = document.getElementById("createRoomButton");
    var joinRoomButton = document.getElementById("joinRoomButton");
    if(newRoomName){
        createRoomButton.disabled = true;
        joinRoomButton.disabled = true;
        roomNameInput.disabled = true;
        sCreateRoom(newRoomName);
    }
}

function generateBoardHTML(serverBoard) {
    var boardRoot = document.getElementsByClassName("board-root")[0];
    boardRoot.innerHTML = "";

    serverBoard.forEach(box => {
        // <div class="board-piece-box">
        //     <div class="board-piece-red"></div>
        // </div>
        var boxObject = document.createElement("div");
        boxObject.className = "board-piece-box";
        if (box.winnerSquare){
            boxObject.classList.add("winnerSquare");
        }
        boxObject.onclick = function() { columnClicked(`${box.column}`); };
        if (box.piece){
            boxObject.innerHTML = `<div class="board-piece-${box.color}"></div>`;
        }
        boardRoot.appendChild(boxObject);
    });
}

function columnClicked(col) {
    var colNum = parseInt(col);
    if (!winner){
        sColumnClicked(colNum);
    }
}
