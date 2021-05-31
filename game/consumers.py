import json, asyncio
from os import confstr, sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import connections
from .models import Board
from channels.db import database_sync_to_async

class WSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
             
    async def disconnect(self, code):
        allBoards = await database_sync_to_async(list)(Board.objects.all())
        for b in allBoards:
            if (b.redPlayer == self.channel_name):
                b.redPlayer = ""
                b.redConnected = False
                await self.channel_layer.group_discard(b.roomName, self.channel_name)
                await database_sync_to_async(b.save)()
            elif(b.yellowPlayer == self.channel_name):
                b.yellowPlayer = ""
                b.yellowConnected = False
                await self.channel_layer.group_discard(b.roomName, self.channel_name)
                await database_sync_to_async(b.save)()
            if (b.redConnected == False and b.yellowConnected == False):
                await database_sync_to_async(b.delete)()
        return await super().disconnect(code)

    async def receive(self, text_data):
        receivingData = json.loads(text_data)
        command = receivingData["command"]
        roomName = receivingData["roomName"]
        roomObject = await self.getRoomObject(roomName)


        if(command == "update"):
            redPlayer = receivingData["redPlayer"]
            yellowPlayer = receivingData["yellowPlayer"]
            colorFlag = roomObject.colorFlag
            if(roomObject.redConnected & roomObject.yellowConnected):
                if(colorFlag == False & redPlayer):
                    roomObject.colorFlag = True
                    # roomObject.boxes = board
                elif(colorFlag & yellowPlayer):
                    roomObject.colorFlag = False
                    # roomObject.boxes = board
                
                await database_sync_to_async(roomObject.save)()
                await self.sendGroupMessage(roomName, "update", json.dumps(roomObject.boxes))
                await self.sendGroupMessage(roomName, "updateColorFlag", roomObject.colorFlag)

        elif(command == "createRoom"):
            print("Create Room")
            if(await self.getRoomObject(roomName)):
                await self.send(json.dumps({
                    "command": "roomError",
                    "data": "Room Name Already Exists"
                }))
            else:
                print("Creating New Room")
                newBoard = await self.generateNewBoard()
                newRoom = Board(boxes=json.dumps(newBoard), roomName=roomName)
                await database_sync_to_async(newRoom.save)()
                await self.send(json.dumps({
                    "command": "joinRoom",
                    "data": newRoom.roomName
                }))

        elif(command == "joinRoom"):
            if(roomObject):
                await self.channel_layer.group_add(roomName, self.channel_name)
                color = "none"
                if(roomObject.redConnected == False):
                    roomObject.redConnected = True
                    roomObject.redPlayer = self.channel_name
                    color = "red"
                elif(roomObject.yellowConnected == False):
                    roomObject.yellowConnected = True
                    roomObject.yellowPlayer = self.channel_name
                    color = "yellow"
                await database_sync_to_async(roomObject.save)()
                await self.send(json.dumps({
                        "command": "assignColor",
                        "data": color
                    }))
                await self.sendGroupMessage(roomName, "initialUpdate", json.dumps(roomObject.boxes))
            else:
                await self.send(json.dumps({
                    "command": "roomError",
                    "data": "Room Name Does Not Exist"
                }))

        elif(command == "columnClicked"):
            redPlayer = receivingData["redPlayer"]
            yellowPlayer = receivingData["yellowPlayer"]
            colorFlag = roomObject.colorFlag
            colNum = receivingData["colNum"]
            board = json.loads(roomObject.boxes)
            boxIndex = -1

            if((colorFlag and yellowPlayer) or ((colorFlag == False) and redPlayer)):
                i = 0
                while i < len(board):
                    if(board[i]["column"] == colNum and board[i]["piece"] == False):
                        if(i > boxIndex):
                            boxIndex = i
                    i+=1

                
                # print(colNum)
                # print(boxIndex)
                if(boxIndex > -1 and roomObject.winner == False):
                    board[boxIndex]["piece"] = True
                    if(colorFlag):
                        board[boxIndex]["color"] = "yellow"
                        colorFlag = False
                    else:
                        board[boxIndex]["color"] = "red"
                        colorFlag = True
                # print(board)
                roomObject.colorFlag = colorFlag
                roomObject.boxes = json.dumps(board)
                await database_sync_to_async(roomObject.save)()
                await self.sendGroupMessage(roomName, "update", roomObject.boxes)
                await self.checkForWinner(roomName)
                    
        elif(command == "resetBoard"):
            newBoard = await self.generateNewBoard()
            roomObject.boxes = json.dumps(newBoard)
            roomObject.colorFlag = False
            roomObject.winner = False
            await database_sync_to_async(roomObject.save)()
            await self.sendGroupMessage(roomName, "initialUpdate", json.dumps(roomObject.boxes))
            await self.sendGroupMessage(roomName, "updateColorFlag", roomObject.colorFlag)
            await self.sendGroupMessage(roomObject.roomName, "resetBoard", "reset")


    async def getRoomObject(self, roomName):
        allBoards = await database_sync_to_async(list)(Board.objects.all())
        for b in allBoards:
            if (b.roomName == roomName):
                return(b)

    async def sendGroupMessage(self, group, command, data):
        await self.channel_layer.group_send(
            group,
            {
                "type": "message",
                "text": json.dumps({
                    "command": command,
                    "data": data
                })
            })

    async def message(self, event):
        await self.send(text_data=event["text"])
        
    async def checkForWinner(self, roomName):
        roomObject = await self.getRoomObject(roomName)
        board = json.loads(roomObject.boxes)
        checkArray = [-8, -7, -6, -1, 1, 6, 7, 8]
        redBoxes = []
        yellowBoxes = []
        i = 0
        while i < len(board):
            if(board[i]["piece"] == True):
                if(board[i]["color"] == "red"):
                    redBoxes.append(i)
                else:
                    yellowBoxes.append(i)
            i+=1
        # print(redBoxes)
        # print(yellowBoxes)
        await self.tallyPoints(redBoxes, checkArray, roomName)
        await self.tallyPoints(yellowBoxes, checkArray, roomName)

    async def tallyPoints(self, boxIndexes, checkArray, roomName):
        # print("tally points")

        for index in boxIndexes:
            for direction in checkArray:
                await self.searchDirection(index, direction, 1, boxIndexes, [], roomName)

    async def searchDirection(self, index, direction, temp, boxIndexes, searchIndexes, roomName):
        searchIndexes.append(index)

        horizontalDirections = [8, -8, 6, -6, 1, -1]
        boardBounds = [0, 7, 14, 21, 28, 35, 6, 13, 20, 27, 34, 41]
        if((direction in horizontalDirections) and (index in boardBounds)):
            pass
        else:
            search = index + direction
            p = temp
            if(search in boxIndexes):
                p+=1
                await self.searchDirection(search, direction, p, boxIndexes, searchIndexes, roomName)
                if(p == 4):
                    roomObject = await self.getRoomObject(roomName)
                    if(roomObject.winner == False):
                        print("Winner")
                        await self.gameWon(searchIndexes, roomName)
        
    async def gameWon(self, indexes, roomName):
        roomObject = await self.getRoomObject(roomName)
        board = json.loads(roomObject.boxes)
        for index in indexes:
            board[index]["winnerSquare"] = True
        roomObject.boxes = json.dumps(board)
        roomObject.winner = True
        await database_sync_to_async(roomObject.save)()
        await self.sendGroupMessage(roomObject.roomName, "update", roomObject.boxes)
        await self.sendGroupMessage(roomObject.roomName, "gameWon", "yay!")
        
    async def generateNewBoard(self):
        newBoard = []
        columnCounter = 0
        i = 0
        while i < 42:
            i+=1
            box = {
                "column": columnCounter,
                "piece": False,
                "color": "",
                "winnerSquare": False
            }

            newBoard.append(box)

            columnCounter+=1
            if (columnCounter == 7):
                columnCounter = 0
        return newBoard