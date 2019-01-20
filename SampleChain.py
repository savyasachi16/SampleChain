#Blockchain Question
#input integer array startBalances
#input array[] pendingTransactions= [fromAddress,toAddress,value]
#input int blockSize
#output string = (blockHash, prevBlockHash, nonce, blockTransactions)

import hashlib


def getLatestBlock(startBalances, pendingTransactions, blockSize):
    currentHash = '0000000000000000000000000000000000000000'

    while (len(pendingTransactions) != 0):
        previousHash = currentHash
        currentTransactions = validateTransactions(startBalances, pendingTransactions, blockSize)
        nonce = findNonce(previousHash, currentTransactions)
        currentHash = findBlockHash(previousHash, currentTransactions,nonce)

    return currentHash + ', ' + previousHash + ', ' + str(nonce) + ', ' + str(currentTransactions)


def sha1(text):
    s = hashlib.sha1()
    s.update(text.encode('utf-8'))
    return s.hexdigest()


def findBlockHash(prevBlockHash, transactions,nonce):
    return sha1(prevBlockHash + ', ' + str(nonce) + ', ' + str(transactions))


def findNonce(prevBlockHash, transactions):
    found = 0
    nonce = 1
    while found == 0:
        hash = sha1(prevBlockHash + ', ' + str(nonce) + ', ' + str(transactions))
        if hash[0:4] == '0000':
            found = 1
            break
        nonce += 1

    return nonce


def validateTransactions(startBalances, pendingTransactions, blockSize):
    approvedTransactions = []
    count = 0
    while (count < blockSize) or pendingTransactions:
        if startBalances[pendingTransactions[0][0]] >= pendingTransactions[0][2]:
            s = approvedTransactions.append(pendingTransactions[0])
            updateBalances(startBalances, pendingTransactions[0])
        del pendingTransactions[0]
        count += 1
    return approvedTransactions


def updateBalances(startBalances, currentTransactions):
    startBalances[currentTransactions[1]] = startBalances[currentTransactions[1]] + currentTransactions[2]
    startBalances[currentTransactions[0]] = startBalances[currentTransactions[0]] - currentTransactions[2]

def main():
    print(getLatestBlock([5, 0, 0], [[0, 1, 5], [1, 2, 5]], 2))

if __name__ == '__main__':
    main()
