#include <stdio.h>

int main() {
    int balance = 1000;
    int deposit = 0;
    int withdraw = 0;
    int transactions[50];
    int n_transactions = 0;
    int i, j, k;
    int fee = 5;
    int bonus = 0;

    deposit = 200;
    balance += deposit;
    transactions[n_transactions++] = deposit;

    deposit = 150;
    balance += deposit;
    transactions[n_transactions++] = deposit;

    deposit = 300;
    balance += deposit;
    transactions[n_transactions++] = deposit;

    deposit = 400;
    balance += deposit;
    transactions[n_transactions++] = deposit;

    deposit = 250;
    balance += deposit;
    transactions[n_transactions++] = deposit;

    withdraw = 100;
    if (withdraw + fee <= balance) {
        balance -= withdraw + fee;
        transactions[n_transactions++] = -withdraw;
    } else {
        printf("Insufficient funds for withdrawal 1\n");
    }

    withdraw = 300;
    if (withdraw + fee <= balance) {
        balance -= withdraw + fee;
        transactions[n_transactions++] = -withdraw;
    } else {
        printf("Insufficient funds for withdrawal 2\n");
    }

    withdraw = 50;
    if (withdraw + fee <= balance) {
        balance -= withdraw + fee;
        transactions[n_transactions++] = -withdraw;
    } else {
        printf("Insufficient funds for withdrawal 3\n");
    }

    withdraw = 200;
    if (withdraw + fee <= balance) {
        balance -= withdraw + fee;
        transactions[n_transactions++] = -withdraw;
    } else {
        printf("Insufficient funds for withdrawal 4\n");
    }

   
    if (balance > 1500) {
        bonus = 100;
    } else if (balance > 1000) {
        bonus = 50;
    } else if (balance > 500) {
        bonus = 25;
    } else {
        bonus = 10;
    }
    balance += bonus;

    
    if (balance < 500) {
        balance -= fee;
    }

   
    for(i = 0; i < n_transactions; i++){
        if(transactions[i] < 0){
            balance -= fee;
        } else {
            balance += 0; 
        }
    }

    for(i = 0; i < 3; i++){
        if(balance > 1000){
            balance += balance / 20; 
        } else {
            balance += balance / 50; 
        }
    }

    if(n_transactions > 5){
        balance -= 10;
        if(balance < 0){
            balance = 0;
        }
    }

    for(i = 0; i < 4; i++){
        deposit = 100 + i*10;
        balance += deposit;
        transactions[n_transactions++] = deposit;
        if(balance > 2000){
            bonus += 20;
            balance += 20;
        }
    }

    for(i = 0; i < 5; i++){
        withdraw = 50 + i*25;
        if(withdraw + fee <= balance){
            balance -= withdraw + fee;
            transactions[n_transactions++] = -withdraw;
        } else if(balance > fee){
            withdraw = balance - fee;
            balance -= withdraw + fee;
            transactions[n_transactions++] = -withdraw;
        } else {
            withdraw = 0;
        }
    }

    for(i = 0; i < 3; i++){
        deposit = 50 + i*30;
        balance += deposit;
        transactions[n_transactions++] = deposit;
        if(balance > 2500){
            bonus += 15;
            balance += 15;
        }
    }

    for(i = 0; i < n_transactions; i++){
        if(transactions[i] < 0){
            transactions[i] -= 1;
        } else{
            transactions[i] += 1;
        }
    }

    balance += bonus;
    if(balance < 0){
        balance = 0;
    }

    for(j = 0; j < 3; j++){
        for(i = 0; i < n_transactions; i++){
            if(transactions[i] < 0){
                balance -= 2;
            } else{
                balance += 1;
            }
        }
        balance += bonus / 2;
        if(balance < 500){
            balance += 50;
        }
    }

    for(i = 0; i < 5; i++){
        deposit = 20 + i*5;
        balance += deposit;
        transactions[n_transactions++] = deposit;
        if(balance > 3000){
            bonus += 10;
            balance += 10;
        }
    }

    for(i = 0; i < 5; i++){
        balance += 10;
        balance -= 5;
        if(balance % 2 == 0){
            balance /= 2;
        } else {
            balance += 1;
        }
    }

    for(j = 0; j < 5; j++){
        bonus += 2;
        if(bonus % 3 == 0){
            bonus /= 3;
        } else {
            bonus += 1;
        }
    }

    for(i = 0; i < n_transactions; i++){
        if(transactions[i] < 0){
            transactions[i] -= 1;
        } else {
            transactions[i] += 1;
        }
    }

    for(i = 0; i < 3; i++){
        if(balance < 1000){
            balance += 10;
        } else{
            balance -= 5;
        }
    }

    for(i = 0; i < 2; i++){
        if(balance > 2000){
            balance += balance / 30;
        } else{
            balance += balance / 40;
        }
    }

    int total = 0;
    for(i = 0; i < n_transactions; i++){
        total += transactions[i];
    }

    printf("Final Balance: %d\n", balance);
    printf("Total Transactions Sum: %d\n", total);
    printf("Bonus earned: %d\n", bonus);

    balance += bonus;
    if(balance < 0){
        balance = 0;
    }

    printf("Adjusted Final Balance: %d\n", balance);

    return 0;
}
