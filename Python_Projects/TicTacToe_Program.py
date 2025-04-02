# Date:  November 30, 2023

#Code taken from Sample Code Neural Tic-Tac-Toe
#Edited by Jonathan Zderad from ChatGPT code created 6/24/2023

import numpy as np
import time

# Define the neural network architecture
class TicTacToeNet:
    def __init__(self):
        self.weights1 = np.random.randn(BOARD_SIZE ** 2, HIDDEN_SIZE)
        self.weights2 = np.random.randn(HIDDEN_SIZE, HIDDEN_SIZE)
        self.weights3 = np.random.randn(HIDDEN_SIZE, BOARD_SIZE ** 2)

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def forward(self, X):
        self.hidden1 = self.sigmoid(np.dot(X, self.weights1))
        self.hidden2 = self.sigmoid(np.dot(self.hidden1, self.weights2))
        self.output = self.sigmoid(np.dot(self.hidden2, self.weights3))
        return self.output

    def train(self, X, y, learning_rate=0.1):
        output = self.forward(X)

        # Backpropagation
        output_error = y - output
        output_delta = output_error * output * (1 - output)

        hidden2_error = np.dot(output_delta, self.weights3.T)
        hidden2_delta = hidden2_error * self.hidden2 * (1 - self.hidden2)

        hidden1_error = np.dot(hidden2_delta, self.weights2.T)
        hidden1_delta = hidden1_error * self.hidden1 * (1 - self.hidden1)

        # Update weights
        self.weights3 += learning_rate * np.dot(self.hidden2.T, output_delta)
        self.weights2 += learning_rate * np.dot(self.hidden1.T, hidden2_delta)
        self.weights1 += learning_rate * np.dot(X.T, hidden1_delta)


# Function to convert the board state to a one-hot encoded representation
def preprocess_board(board):
    one_hot = np.zeros((BOARD_SIZE ** 2,))
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] == 'X':
                one_hot[i * BOARD_SIZE + j] = 1
            elif board[i][j] == 'O':
                one_hot[i * BOARD_SIZE + j] = -1
    return one_hot


# Function to make a move based on the current board state
def make_move(board, player):
    flattened_board = preprocess_board(board).reshape(1, BOARD_SIZE ** 2)
    predictions = net.forward(flattened_board)[0]
    flat = []
    flat.append(board[0][0])
    flat.append(board[0][1])
    flat.append(board[0][2])
    flat.append(board[1][0])
    flat.append(board[1][1])
    flat.append(board[1][2])
    flat.append(board[2][0])
    flat.append(board[2][1])
    flat.append(board[2][2])
    valid_moves = [i for i, value in enumerate(flat) if value == ' ']
    valid_predictions = [predictions[i] for i in valid_moves]
    print('calculations for choices')
    print(predictions[0:3])
    print(predictions[3:6])
    print(predictions[6:9])
    print()
    best_move = valid_moves[np.argmax(valid_predictions)]
    row = best_move // BOARD_SIZE
    col = best_move % BOARD_SIZE
    board[row][col] = player

def person_move(board, player):
    row = int(input("Enter Row:"))
    col = int(input("Enter Column:"))
    board[row][col] = player

def determineWinner():
    winner = False
    #diagonals
    if (board[0][0]==board[1][1]==board[2][2]) and (board[0][0]!=' '):
        return True
    elif (board[2][0] == board[1][1] == board[0][2]) and (board[2][0] != ' '):
        return True
    #vertical
    elif (board[0][0] == board[1][0] == board[2][0]) and (board[0][0] != ' '):
        return True
    elif (board[0][1] == board[1][1] == board[2][1]) and (board[0][1] != ' '):
        return True
    elif (board[0][2] == board[1][2] == board[2][2]) and (board[0][2] != ' '):
        return True
    #horizontal
    elif (board[0][0] == board[0][1] == board[0][2]) and (board[0][0] != ' '):
        return True
    elif (board[1][0] == board[1][1] == board[1][2]) and (board[1][0] != ' '):
        return True
    elif (board[2][0] == board[2][1] == board[2][2]) and (board[2][0] != ' '):
        return True
    else:
        return False
# Training the model
def train_model():
    # Example training data
    # In this case, 'X' wins by placing three 'X's in a row
    X_train = [[['X', ' ', ' '],
                ['O', 'X', 'O'],
                ['X', ' ', ' ']]]
    Y_train = [[0,0,1,0,0,0,0,0,1]]
    X_train += [[['X', ' ', ' '],
                 ['O', 'X', 'O'],
                 [' ', ' ', ' ']]]
    Y_train += [[0,0,0,0,0,0,0,0,1]]
    X_train += [[['X', ' ', 'O'],
                 ['O', 'X', 'O'],
                 ['X', ' ', ' ']]]
    Y_train += [[0,0,0,0,0,0,0,0,1]]
    X_train += [[['X', ' ', ' '],
                 ['X', 'O', 'O'],
                 [' ', ' ', ' ']]]
    Y_train += [[0,0,0,0,0,0,1,0,0]]
    X_train +=  [[['O', ' ', ' '],
                  ['O', 'X', ' '],
                  ['X', ' ', 'X']]]
    Y_train += [[0,0,1,0,0,0,0,1,0]]
    X_train +=  [[['O', 'X', ' '],
                  ['X', 'O', ' '],
                  ['O', 'X', ' ']]]
    Y_train += [[0,0,1,0,0,0,0,0,1]]
    X_train +=  [[['X', ' ', 'O'],
                  ['O', 'X', 'O'],
                  ['X', ' ', ' ']]]
    Y_train += [[0,0,0,0,0,0,0,0,1]]
    X_train += [[['X', 'O', ' '],
                 [' ', ' ', 'O'],
                 [' ', ' ', 'X']]]
    Y_train += [[0,0,0,0,1,0,0,0,0]]
    X_train += [[['O', 'X', 'O'],
                 ['X', ' ', 'X'],
                 ['O', ' ', 'O']]]
    Y_train += [[0,0,0,0,1,0,0,0,0]]
    X_train += [[['X', 'O', 'X'],
                 [' ', 'O', ' '],
                 ['X', 'X', 'O']]]
    Y_train += [[0,0,0,1,0,0,0,0,0]]
    X_train += [[['O', 'O', 'X'],
                 [' ', 'X', ' '],
                 ['X', ' ', 'O']]]
    Y_train += [[0,0,0,1,0,1,0,0,0]]
    X_train +=  [[['X', 'X', 'O'],
                  ['X', 'O', 'X'],
                  [' ', 'X', 'O']]]
    Y_train += [[0,0,0,0,0,0,1,0,0]]
    X_train += [[['O', 'O', 'X'],
                 ['O', 'X', 'X'],
                 ['X', 'O', ' ']]]
    Y_train += [[0,0,0,0,0,0,0,0,1]]
    X_train += [[['X', 'O', 'X'],
                 ['O', ' ', 'O'],
                 ['O', 'O', 'X']]]
    Y_train += [[0,0,0,0,1,0,0,0,0]]
    X_train += [[['O', 'X', 'X'],
                 [' ', 'X', 'O'],
                 ['O', 'O', 'X']]]
    Y_train += [[0,0,0,1,0,0,0,0,0]]
    X_train += [[['O', 'X', ' '],
                 ['X', 'O', 'O'],
                 ['X', ' ', 'X']]]
    Y_train += [[0,0,0,0,0,0,0,1,0]]
    X_train +=  [[['X', 'O', 'X'],
                  ['O', 'X', 'O'],
                  ['X', ' ', 'O']]]
    Y_train += [[0,0,0,0,0,0,0,1,0]]
    X_train +=  [[['O', 'X', 'O'],
                  ['X', 'O', 'X'],
                  [' ', 'X', 'O']]]
    Y_train += [[0,0,0,0,0,0,1,0,0]]
    X_train +=    [[['X', 'O', 'O'],
                    ['X', 'X', 'O'],
                    ['O', 'X', ' ']]]
    Y_train += [[0,0,0,0,0,0,0,0,1]]
    X_train += [[['X', ' ', 'X'],
                 ['O', 'O', ' '],
                 ['O', 'X', ' ']]]
    Y_train += [[0,1,0,0,0,0,0,0,0]]
    X_train +=  [[['X', 'O', 'X'],
                  ['O', ' ', 'X'],
                  ['O', 'X', 'O']]]
    Y_train += [[0,0,0,0,1,0,0,0,0]]
    X_train +=   [[['O', 'X', 'O'],
                   ['O', 'O', 'X'],
                   ['X', 'X', ' ']]]
    Y_train += [[0,0,0,0,0,0,0,0,1]]
    X_train += [[['O', 'X', 'X'],
                 [' ', 'X', 'O'],
                 ['X', 'O', 'O']]]
    Y_train += [[0,0,0,1,0,0,0,0,0]]
    #start of aditional training
    X_train = [[['X', ' ', ' '],
                ['O', ' ', ' '],
                ['X', ' ', '0']]]
    Y_train = [[0,0,1,0,0,0,0,0,0]]
    X_train = [[['X', ' ', ' '],
                ['0', ' ', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[0,0,1,0,0,0,0,0,1]]
    X_train = [[[' ', ' ', 'X'],
                [' ', ' ', '0'],
                [' ', ' ', ' ']]]
    Y_train = [[1, 0, 0, 0, 0, 0, 1, 0, 0]]
    X_train = [[['X', ' ', ' '],
                [' ', ' ', ' '],
                [' ', ' ', '0']]]
    Y_train = [[0, 0, 1, 0, 0, 0, 1, 0, 0]]
    X_train = [[['X', '0', 'X'],
                [' ', ' ', ' '],
                [' ', ' ', '0']]]
    Y_train = [[0, 0, 0, 0, 0, 0, 1, 0, 0]]
    X_train = [[['X', '0', 'X'],
                [' ', '0', ' '],
                ['X', ' ', '0']]]
    Y_train = [[0, 0, 0, 1, 0, 0, 0, 0, 0]]
    X_train = [[['0', ' ', 'X'],
                [' ', ' ', ' '],
                ['X', ' ', '0']]]
    Y_train = [[0, 0, 0, 0, 1, 0, 0, 0, 0]]
    X_train = [[['X', ' ', '0'],
                [' ', ' ', ' '],
                ['0', ' ', 'X']]]
    Y_train = [[0, 0, 0, 0, 1, 0, 0, 0, 0]]
    X_train = [[['0', '0', ' '],
                [' ', ' ', ' '],
                ['X', 'X', ' ']]]
    Y_train = [[0, 0, 1, 0, 0, 0, 0, 0, 0]]
    X_train = [[['0', '0', 'X'],
                [' ', ' ', ' '],
                ['X', 'X', '0']]]
    Y_train = [[0, 0, 0, 0, 1, 0, 0, 0, 0]]
    X_train = [[[' ', ' ', '0'],
                [' ', 'X', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[1, 0, 0, 0, 0, 0, 0, 0, 0]]
    X_train = [[['X', ' ', '0'],
                [' ', 'X', ' '],
                [' ', ' ', '0']]]
    Y_train = [[0, 0, 0, 0, 0, 1, 0, 0, 0]]
    X_train = [[[' ', 'X', ' '],
                [' ', '0', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[0, 0, 1, 0, 0, 0, 0, 0, 0]]
    X_train = [[['0', 'X', 'X'],
                [' ', '0', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[0, 0, 0, 0, 0, 0, 0, 0, 1]]
    X_train = [[['X', ' ', 'O'],
                [' ', 'O', ' '],
                ['X', ' ', ' ']]]
    Y_train = [[0, 0, 0, 1, 0, 0, 0, 0, 0]]
    X_train = [[['0', ' ', 'X'],
                [' ', 'O', ' '],
                [' ', ' ', 'X']]]
    Y_train = [[0, 0, 0, 0, 0, 1, 0, 0, 0]]
    X_train = [[['0', 'X', 'X'],
                ['X', ' ', ' '],
                ['0', ' ', '0']]]
    Y_train = [[0, 0, 0, 0, 1, 0, 0, 0, 0]]
    X_train = [[[' ', ' ', '0'],
                ['X', ' ', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[1, 0, 0, 0, 0, 0, 1, 0, 1]]
    X_train = [[['0', ' ', ' '],
                [' ', ' ', 'X'],
                [' ', ' ', ' ']]]
    Y_train = [[0, 0, 1, 0, 0, 0, 1, 0, 1]]
    X_train = [[['X', ' ', '0'],
                [' ', ' ', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[0, 0, 0, 0, 0, 0, 1, 0, 1]]
    X_train = [[['0', ' ', 'X'],
                [' ', ' ', ' '],
                [' ', ' ', ' ']]]
    Y_train = [[0, 0, 0, 0, 0, 0, 1, 0, 1]]
    X_train = [[['0', ' ', ' '],
                [' ', ' ', ' '],
                [' ', ' ', 'X']]]
    Y_train = [[0, 0, 1, 0, 0, 0, 1, 0, 0]]
    X_train = [[[' ', ' ', ' '],
                ['X', ' ', '0'],
                [' ', ' ', ' ']]]
    Y_train = [[0, 0, 1, 0, 0, 1, 0, 0, 0]]
    X_train = [[['0', 'X', ' '],
                [' ', '0', ' '],
                ['0', 'X', 'X']]]
    Y_train = [[0, 0, 0, 1, 0, 0, 0, 0, 0]]
    X_train = [[[' ', 'X', '0'],
                [' ', '0', ' '],
                ['X', 'X', '0']]]
    Y_train = [[0, 0, 0, 0, 0, 1, 0, 0, 0]]
    X_train = [[[' ', ' ', 'X'],
                [' ', ' ', 'X'],
                ['0', ' ', '0']]]
    Y_train = [[0, 0, 0, 0, 0, 0, 0, 1, 0]]
    X_train = [[['0', ' ', 'X'],
                [' ', ' ', 'X'],
                ['0', 'X', '0']]]
    Y_train = [[0, 0, 0, 1, 0, 0, 0, 0, 0]]
    X_train = [[[' ', ' ', 'X'],
                [' ', 'X', ' '],
                ['0', ' ', '0']]]
    Y_train = [[0, 0, 0, 0, 0, 0, 0, 1, 0]]
    X_train = [[['0', ' ', '0'],
                ['X', ' ', ' '],
                ['X', ' ', ' ']]]
    Y_train = [[0, 1, 0, 0, 0, 0, 0, 0, 0]]
    X_train = [[['0', ' ', '0'],
                [' ', ' ', 'X'],
                [' ', ' ', 'X']]]
    Y_train = [[0, 1, 0, 0, 0, 0, 0, 0, 0]]
    net = TicTacToeNet()

    for _ in range(TRAINING_ITERATIONS):  # Perform 10 training iterations
        for board, move in zip(X_train, Y_train):
            flattened_board = preprocess_board(board).reshape(1, BOARD_SIZE ** 2)
            target = np.array([move])
            net.train(flattened_board, target)


# Example usage
# Define the tic-tac-toe board size
BOARD_SIZE = 3
HIDDEN_SIZE = 16
TRAINING_ITERATIONS = 10
print("Creating Board...")
board = [[' ', ' ', ' '],
         [' ', ' ', ' '],
         [' ', ' ', ' ']]
print(board)
time.sleep(2)

print("\nCreating Model ...")
print("\nInputs   Hidden1  Hidden2  Outputs")
print("      -->  J1  -->  K1  -->        ")
print("      -->  J2  -->  K2  -->       ")
print("      -->  J3  -->  K3  -->       ")
print("  I1  -->  J4  -->  K4  -->  O1")
print("  I2  -->  J5  -->  K5  -->  O2")
print("  I3  -->  J6  -->  K6  -->  O3")
print("  I4  -->  J7  -->  K7  -->  O4")
print("  I5  -->  J8  -->  K8  -->  O5")
print("  I6  -->  J9  -->  K9  -->  O6")
print("  I7  -->  J10 -->  K10 -->  O7")
print("  I8  -->  J11 -->  K11 -->  O8")
print("  I9  -->  J12 -->  K12 -->  O9")
print("      -->  J13 -->  K13 -->         ")
print("      -->  J14 -->  K14 -->        ")
print("      -->  J15 -->  K15 -->        ")
print("      -->  J16 -->  K16 -->        ")
time.sleep(2)
print("\nTraining Model ...")
net = TicTacToeNet()
train_model()
time.sleep(2)

print("\nReady to Play ...")
print()
player = 'X'
for j in range(9):
    if player == 'X':
        make_move(board, 'X')  # Neural network makes a move as 'X'
    else:
        person_move(board, 'O')  # Person moves as 'O'
    print(np.array(board))
    print()
    if determineWinner() == True:
        print(player, "wins")
        exit(0);
    if player == 'X':
        player = 'O'
    else:
        player = 'X'
