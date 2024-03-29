#!/bin/env python3

import pygame
import random
import game
import numpy as np
import minimax_abPrunning as minimax


class GameState():
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp",],
            ["--", "--", "--", "--", "--", "--", "--", "--",],
            ["--", "--", "--", "--", "--", "--", "--", "--", ],
            ["--", "--", "--", "--", "--", "--", "--", "--", ],
            ["--", "--", "--", "--", "--", "--", "--", "--", ],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp", ],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.whiteToMove = True
        self.moveLog = []
        self.undoneMoves = []
        self.whiteKingLocation = (4, 7)
        self.blackKingLocation = (4, 0)
        self.moveFunctions = {'p': self.pawnMoves, 'N': self.knightMoves, 'B': self.bishopMoves,
                              'R': self.rockMoves, 'Q': self.queenMoves, 'K': self.kingMoves}
        self.castlingRightsLog = [Castling(True, True, True, True)]
        self.boardLog = [self.boardCopy()]
        self.fiftyMoves = 0
        self.canKillPassantLog = []

    def boardCopy(self):
        return [x[:] for x in self.board]

    def arrayBoard(self):
        return [piece for row in self.board for piece in row]

    def piecesInBoard(self):
        pieces = [piece for row in self.board for piece in row]
        pieces = list(filter("--".__ne__, pieces))
        return pieces

    def piecesAsNumbers(self):
        mapBoard = {"wp": 1, "wN": 2, "wB": 3, "wR": 4, "wQ": 5, "wK": 6, "bp": -1, "bN": -2, "bB": -3, "bR": -4, "bQ": -5, "bK": -6}
        pieces = self.piecesInBoard()
        pieces = np.array([mapBoard[piece] for piece in pieces])
        return pieces

    def boardAsNumbers(self):
        mapBoard = {"--": 0, "wp": 1, "wN": 2, "wB": 3, "wR": 4, "wQ": 5, "wK": 6, "bp": -1, "bN": -2, "bB": -3, "bR": -4, "bQ": -5, "bK": -6}
        pieces = [piece for row in self.board for piece in row]
        board = np.array([mapBoard[piece] for piece in pieces])
        return board

    def makeMove(self, move):
        player = game.playerWhite if self.whiteToMove else game.playerBlack
        moves, movesID = self.getValidMoves()
        print(movesID)
        if move.moveID in movesID and not self.undoneMoves:
            self.canKillPassantLog.append(self.canKillPassant(moves))
            move.isCastleMove = self.isCastleMove(move, moves)
            move.isEnPassantMove = self.isPassantMove(move, moves)
            move.isPromotionMove = self.isPromotionMove(move, moves)
            if move.isPromotionMove and player == "human":
                move.piecePromoted = move.pieceMoved[0] + self.humanPickPromotionPiece()
            elif move.isPromotionMove and player != "human":
                move.piecePromoted = self.pickPromotionPiece(player, move)
            print(move.moveID)
            self.movePiece(move)
            self.boardLog.append(self.boardCopy())
            if move.pieceCaptured != "--" or move.pieceMoved[1] == "p":
                self.fiftyMoves = 0
            else:
                self.fiftyMoves += 1
            self.piecesInBoard()

    def isCastleMove(self, move, moves):
        for i in range(len(moves) - 1, -1, -1):
            if move.moveID == moves[i].moveID:
                return moves[i].isCastleMove
        return False

    def isPassantMove(self, move, moves):
        for i in range(len(moves) - 1, -1, -1):
            if move.moveID == moves[i].moveID:
                return moves[i].isEnPassantMove
        return False

    def isPromotionMove(self, move, moves):
        for i in range(len(moves) - 1, -1, -1):
            if move.moveID == moves[i].moveID:
                return moves[i].isPromotionMove
        return False

    def humanPickPromotionPiece(self):
        picked = False
        piece = "p"
        while not picked:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        piece = "Q"
                        picked = True
                    elif event.key == pygame.K_r:
                        piece = "R"
                        picked = True
                    elif event.key == pygame.K_b:
                        piece = "B"
                        picked = True
                    elif event.key == pygame.K_n:
                        piece = "N"
                        picked = True
        return piece

    def pickPromotionPiece(self, player, move):
        color = "w" if self.whiteToMove else "b"
        pieces = ["Q", "N", "B", "R"]
        if player == "random":
            return color + pieces[random.randint(0, 3)]
        if player == "minimax":
            maxVal = -9999
            pieceToPromote = "-"
            for piece in pieces:
                move.piecePromoted = color + piece
                self.movePiece(move)
                eval = -minimax.evaluation(self)
                self.undoMove()
                if eval > maxVal:
                    maxVal = eval
                    pieceToPromote = piece
            return color + pieceToPromote
        if player == "alpha":
            return move.piecePromoted

    def changeKingLocation(self, move, col, row):
        if move.pieceMoved[0] == "w":
            self.whiteKingLocation = (col, row)
        elif move.pieceMoved[0] == "b":
            self.blackKingLocation = (col, row)

    def movePiece(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)  # append the move so it can be undone later
        self.updateCastlingRights(move)  # store the information about castling rights
        self.whiteToMove = not self.whiteToMove  # swap players
        if move.pieceMoved[1] == "K":
            self.changeKingLocation(move, move.endCol, move.endRow)
        if move.isCastleMove:
            self.doCastling(move.startRow, move.startCol, (move.endCol-move.startCol)//2, move, move.pieceMoved[0])
        if move.isEnPassantMove:
            self.doPassant(move)
        if move.isPromotionMove:
            self.doPromotion(move)

    def undoMove(self):
        move = self.moveLog.pop()
        self.castlingRightsLog.pop()
        self.board[move.startRow][move.startCol] = move.pieceMoved
        self.board[move.endRow][move.endCol] = move.pieceCaptured
        self.whiteToMove = not self.whiteToMove  # swap players
        if move.pieceMoved[1] == "K":
            self.changeKingLocation(move, move.startCol, move.startRow)
        if move.isCastleMove:
            self.undoCastling(move.startRow, move.startCol, (move.endCol-move.startCol)//2, move, move.pieceMoved[0])
        if move.isEnPassantMove:
            self.undoPassant(move)

    def goBackMove(self):
        if len(self.moveLog) > 0:
            move = self.moveLog.pop()
            self.undoneMoves.append(move)
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            if move.isCastleMove:
                self.undoCastling(move.startRow, move.startCol, (move.endCol - move.startCol) // 2, move, move.pieceMoved[0])
            if move.isEnPassantMove:
                self.undoPassant(move)

    def goForthMove(self):
        if len(self.undoneMoves) > 0:
            move = self.undoneMoves.pop()
            self.moveLog.append(move)
            self.board[move.startRow][move.startCol] = "--"
            self.board[move.endRow][move.endCol] = move.pieceMoved
            if move.isCastleMove:
                self.doCastling(move.startRow, move.startCol, (move.endCol - move.startCol) // 2, move, move.pieceMoved[0])
            if move.isEnPassantMove:
                self.doPassant(move)
            if move.isPromotionMove:
                self.doPromotion(move)

    def allPossibleMoves(self):
        moves = []
        movesID = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                player = self.board[r][c][0]
                if(player == "w" and self.whiteToMove) or (player == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves, movesID)
        return moves, movesID

    def possiblePieceMoves(self, r, c):
        moves = []
        movesID = []
        player = self.board[r][c][0]
        if (player == "w" and self.whiteToMove) or (player == "b" and not self.whiteToMove):
            piece = self.board[r][c][1]
            self.moveFunctions[piece](r, c, moves, movesID)
        for i in range(len(moves)-1, -1, -1): #when removing from a list go backwards through that list:
            if not self.isValidMove(moves[i]):
                moves.remove(moves[i])
                movesID.remove(movesID[i])
        return moves, movesID

    def pawnMoves(self, r, c, moves, movesID):
        if self.whiteToMove: #white pawn moves
            if self.board[r-1][c] == "--":
                move = Move((c, r), (c, r-1), self.board)
                moves.append(move)
                movesID.append(move.moveID)
                if move.endRow == 0:
                    self.getPromotionMoves(r, c, moves, movesID, "w")
                if r == 6 and self.board[r-2][c] == "--":
                    move = Move((c, r), (c, r-2), self.board)
                    moves.append(move)
                    movesID.append(move.moveID)
            if c - 1 >= 0: #capture to left
                if self.board[r-1][c-1][0] == "b": #enemy to capture
                    move = Move((c, r), (c-1, r-1), self.board)
                    moves.append(move)
                    movesID.append(move.moveID)
                    if move.endRow == 0:
                        self.getPromotionMoves(r, c, moves, movesID, "w")
            if c + 1 <= 7:  # capture to left
                if self.board[r-1][c+1][0] == "b":  # enemy to capture
                    move = Move((c, r), (c+1, r-1), self.board)
                    moves.append(move)
                    movesID.append(move.moveID)
                    if move.endRow == 0:
                        self.getPromotionMoves(r, c, moves, movesID, "w")
            if r == 3:
                self.getPassantMoves(r, c, moves, movesID)
        else: #black pawn moves
            if self.board[r+1][c] == "--":
                move = Move((c, r), (c, r+1), self.board)
                moves.append(move)
                movesID.append(move.moveID)
                if move.endRow == 7:
                    self.getPromotionMoves(r, c, moves, movesID, "b")
                if r == 1 and self.board[r+2][c] == "--":
                    move = Move((c, r), (c, r+2), self.board)
                    moves.append(move)
                    movesID.append(move.moveID)
            if c - 1 >= 0: #capture to left
                if self.board[r+1][c-1][0] == "w": #enemy to capture
                    move = Move((c, r), (c-1, r+1), self.board)
                    moves.append(move)
                    movesID.append(move.moveID)
                    if move.endRow == 7:
                        self.getPromotionMoves(r, c, moves, movesID, "b")
            if c + 1 <= 7:  # capture to left
                if self.board[r+1][c+1][0] == "w":  # enemy to capture
                    move = Move((c, r), (c+1, r+1), self.board)
                    moves.append(move)
                    movesID.append(move.moveID)
                    if move.endRow == 7:
                        self.getPromotionMoves(r, c, moves, movesID, "b")
            if r == 4:
                self.getPassantMoves(r, c, moves, movesID)

    def getPromotionMoves(self, r, c, moves, movesID, color):
        move = moves.pop()
        movesID.pop()
        possiblePieces = ["N", "B", "R", "Q"]
        for piece in possiblePieces:
            promotionMove = Move((c, r), (move.endCol, move.endRow), self.board, False, False, True, color + piece)
            moves.append(promotionMove)
            movesID.append(promotionMove.moveID)


    def doPromotion(self, move):
        self.board[move.endRow][move.endCol] = move.piecePromoted

    def getPassantMoves(self, r, c, moves, movesID):
        lastMove = self.moveLog[-1]  #will not be empty
        if r == 3 and lastMove.pieceMoved == "bp":
            if lastMove.startRow == r-2 and lastMove.endRow == r and (lastMove.endCol == c+1 or lastMove.endCol == c-1):
                move = Move((c, r), (lastMove.endCol, r - 1), self.board, False, True)
                moves.append(move)
                movesID.append(move.moveID)
        if r == 4 and lastMove.pieceMoved == "wp":
            if lastMove.startRow == r+2 and lastMove.endRow == r and (lastMove.endCol == c+1 or lastMove.endCol == c-1):
                move = Move((c, r), (lastMove.endCol, r + 1), self.board, False, True)
                moves.append(move)
                movesID.append(move.moveID)

    def doPassant(self, move):
        if move.startRow == 3:
            self.board[move.endRow + 1][move.endCol] = "--"
        if move.startRow == 4:
            self.board[move.endRow - 1][move.endCol] = "--"

    def undoPassant(self, move):
        if move.startRow == 3:
            self.board[move.endRow + 1][move.endCol] = "bp"
        if move.startRow == 4:
            self.board[move.endRow - 1][move.endCol] = "wp"

    def knightMoves(self, r, c, moves, movesID):
        enemyColor = "b" if self.whiteToMove else "w"
        knightJumps = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
        for jump in knightJumps:
            self.getMove(r, c, moves, movesID, jump[0], jump[1], enemyColor)

    def bishopMoves(self, r, c, moves, movesID):
        enemyColor = "b" if self.whiteToMove else "w"
        directions = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
        for dir in directions:
            for i in range(1, 8):
                endRow = r + dir[0] * i
                endCol = c + dir[1] * i
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    if self.board[endRow][endCol] == "--":
                        move = Move((c, r), (endCol, endRow), self.board)
                        moves.append(move)
                        movesID.append(move.moveID)
                    elif self.board[endRow][endCol][0] == enemyColor:
                        move = Move((c, r), (endCol, endRow), self.board)
                        moves.append(move)
                        movesID.append(move.moveID)
                        break
                    else: #Friendly piece
                        break

    def rockMoves(self, r, c, moves, movesID):
        enemyColor = "b" if self.whiteToMove else "w"
        directions = [(1, 0), (0, -1), (-1, 0), (0, 1)]
        for dir in directions:
            for i in range(1, 8):
                endRow = r + dir[0] * i if dir[0] != 0 else r
                endCol = c + dir[1] * i if dir[1] != 0 else c
                if 0 <= endRow <= 7 and 0 <= endCol <= 7:
                    if self.board[endRow][endCol] == "--":
                        move = Move((c, r), (endCol, endRow), self.board)
                        moves.append(move)
                        movesID.append(move.moveID)
                    elif self.board[endRow][endCol][0] == enemyColor:
                        move = Move((c, r), (endCol, endRow), self.board)
                        moves.append(move)
                        movesID.append(move.moveID)
                        break
                    else:  # Friendly piece
                        break

    def queenMoves(self, r, c, moves, movesID):
        self.bishopMoves(r, c, moves, movesID)
        self.rockMoves(r, c, moves, movesID)

    def kingMoves(self, r, c, moves, movesID):
        enemyColor = "b" if self.whiteToMove else "w"
        kingMoves = [(1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
        for move in kingMoves:
            self.getMove(r, c, moves, movesID, move[0], move[1], enemyColor)
        self.getCastlingMoves(r, c, moves, movesID)

    def getCastlingMoves(self, r, c, moves, movesID):
        if (r == 7 and c == 4) or (r == 0 and c == 4):
                shortCastle = Move((c, r), (c + 2, r), self.board, True)
                moves.append(shortCastle)
                movesID.append(shortCastle.moveID)
                largeCastle = Move((c, r), (c - 2, r), self.board, True)
                moves.append(largeCastle)
                movesID.append(largeCastle.moveID)

    def doCastling(self, r, c, x, move, color):
        if x == 1:
            self.board[r][c+3*x] = "--"
            self.board[move.endRow][move.endCol - x] = color + "R"
        elif x == -1:
            self.board[r][c+4*x] = "--"
            self.board[move.endRow][move.endCol - x] = color + "R"

    def undoCastling(self, r, c, x, move, color):
        if x == 1:
            self.board[r][c+3*x] = color + "R"
            self.board[move.endRow][move.endCol - x] = "--"
        elif x == -1:
            self.board[r][c+4*x] = color + "R"
            self.board[move.endRow][move.endCol - x] = "--"

    def getMove(self, r, c, moves, movesID, x, y, enemyColor):
        if 0 <= r+x <= 7 and 0 <= c+y <= 7:
            if self.board[r+x][c+y] == "--" or self.board[r+x][c+y][0] == enemyColor:
                move = Move((c, r), (c+y, r+x), self.board)
                moves.append(move)
                movesID.append(move.moveID)

    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[1], self.whiteKingLocation[0])
        else:
            return self.squareUnderAttack(self.blackKingLocation[1], self.blackKingLocation[0])

    def inCheckMate(self):
        return self.inCheck() and self.notMoreMoves()

    def notMoreMoves(self):
        moves, movesID = self.getValidMoves()
        return not moves

    def threefoldRepetition(self):
        lastPosition = self.boardLog[-1]
        lastCastleRules = self.castlingRightsLog[-1]
        repeatedTimes = 1
        for i in range(len(self.boardLog) - 1):
            if lastPosition == self.boardLog[i] and lastCastleRules.__dict__ == self.castlingRightsLog[i].__dict__ and not self.canKillPassantLog[i]:
                repeatedTimes += 1  # will be at least 1 cause lastPosition is in boardLog
                print(repeatedTimes)
        return repeatedTimes == 3

    def insufficientMaterial(self):
        pieces = self.piecesInBoard()
        if len(pieces) == 2:  # only the two kings are on the board
            return True
        elif len(pieces) == 3:
            piece = "--"
            for p in range(len(pieces)):
                if pieces[p][1] != "K":
                    piece = pieces[p]
            if piece[1] == "N" or piece[1] == "B":
                return True
        return False

    def itsDraw(self):
        return (self.notMoreMoves() and not self.inCheck()) or self.threefoldRepetition() or self.fiftyMoves == 50 or self.insufficientMaterial()

    def canKillPassant(self, moves):
        for move in moves:
            if self.isPassantMove(move, moves):
                return True
        return False

    def squareUnderAttack(self, row, col):
        self.whiteToMove = not self.whiteToMove #switch to opponent's turn
        oppMoves, oppMovesID = self.allPossibleMoves()
        self.whiteToMove = not self.whiteToMove #switch back the turns
        for move in oppMoves:
            if move.endCol == col and move.endRow == row:
                return True
        return False

    def canCastle(self, move):
        castlingRights = self.castlingRightsLog[-1]
        if move.pieceMoved[0] == "w":
            if move.startRow == 7 and move.startCol == 4:
                if move.endRow == 7 and move.endCol == 6:
                    if self.board[7][5] == "--" and self.board[7][6] == "--":
                        if not self.inCheck() and not self.squareUnderAttack(7, 5) and not self.squareUnderAttack(7, 6):
                            return castlingRights.wKs
                if move.endRow == 7 and move.endCol == 2:
                    if self.board[7][3] == "--" and self.board[7][2] == "--" and self.board[7][1] == "--":
                        if not self.inCheck() and not self.squareUnderAttack(7, 3) and not self.squareUnderAttack(7, 2):
                            return castlingRights.wQs
        if move.pieceMoved[0] == "b":
            if move.startRow == 0 and move.startCol == 4:
                if move.endRow == 0 and move.endCol == 6:
                    if self.board[0][5] == "--" and self.board[0][6] == "--":
                        if not self.inCheck() and not self.squareUnderAttack(0, 5) and not self.squareUnderAttack(0, 6):
                            return castlingRights.bKs
                if move.endRow == 0 and move.endCol == 2:
                    if self.board[0][3] == "--" and self.board[0][2] == "--" and self.board[0][1] == "--":
                        if not self.inCheck() and not self.squareUnderAttack(0, 3) and not self.squareUnderAttack(0, 2):
                            return castlingRights.bQs
        return False

    def getValidMoves(self):
        moves, movesID = self.allPossibleMoves()
        for i in range(len(moves)-1, -1, -1): #when removing from a list go backwards through that list
            if moves[i].isCastleMove:
                if not self.canCastle(moves[i]):
                    moves.remove(moves[i])
                    movesID.remove(movesID[i])
            else:
                # check that your king is not in check in next move
                self.movePiece(moves[i])
                self.whiteToMove = not self.whiteToMove
                if self.inCheck():
                    moves.remove(moves[i])
                    movesID.remove(movesID[i])
                self.whiteToMove = not self.whiteToMove
                self.undoMove()
        return moves, movesID

    def isValidMove(self, move):
        moves, movesID = self.getValidMoves()
        for id in movesID:
            if move.moveID == id:
                return True
        return False

    def updateCastlingRights(self, move):
        castlingRights = Castling(self.castlingRightsLog[-1].wKs, self.castlingRightsLog[-1].wQs, self.castlingRightsLog[-1].bKs, self.castlingRightsLog[-1].bQs)
        if move.pieceMoved == "wK":
            castlingRights.wKs = False
            castlingRights.wQs = False
        elif move.pieceMoved == "bK":
            castlingRights.bKs = False
            castlingRights.bQs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7 and move.startCol == 7:
                castlingRights.wKs = False
            elif move.startRow == 0 and move.startCol == 7:
                castlingRights.wQs = False
        elif move.pieceMoved == "bR":
            if move.startRow == 7 and move.startCol == 0:
                castlingRights.bKs = False
            elif move.startRow == 0 and move.startCol == 0:
                castlingRights.bQs = False
        self.castlingRightsLog.append(castlingRights)

    ''' At depth 5 takes a bit of time '''
    def countPositions(self, depth):
        if depth == 0:
            return 1
        moves, movesID = self.getValidMoves()
        totalPos = 0
        for move in moves:
            self.movePiece(move)
            totalPos += self.countPositions(depth - 1)
            self.undoMove()
        return totalPos

    def getValidMoveIndexes(self):
        moves, movesID = self.getValidMoves()
        return [i for i in range(len(moves))]

    def getBoardSize(self):
        return len(self.board), len(self.board)

    def getCurrentBoard(self):
        return self.board


    def getActionSize(self):
        moves, movesID = self.getValidMoves()
        return len(moves)

class Castling():
    def __init__(self, wKs, wQs, bKs, bQs):
        self.wKs = wKs
        self.wQs = wQs
        self.bKs = bKs
        self.bQs = bQs


class Move():
    rowNotation = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToNotation = {v: k for k, v in rowNotation.items()}
    colNotation = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToNotation = {v: k for k, v in colNotation.items()}

    def __init__(self, startSq, endSq, board, isCastle = False, isEnPassant = False, isPromotion = False, piecePromoted = "--"):
        self.startRow = startSq[1]
        self.startCol = startSq[0]
        self.endRow = endSq[1]
        self.endCol = endSq[0]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.getChessNotation()
        self.isCastleMove = isCastle
        self.isEnPassantMove = isEnPassant
        self.isPromotionMove = isPromotion
        self.piecePromoted = piecePromoted

    def getChessNotation(self):
        return self.getSquare(self.startRow, self.startCol) + self.getSquare(self.endRow, self.endCol)

    def getSquare(self, r, c):
        return self.colsToNotation[c] + self.rowsToNotation[r]