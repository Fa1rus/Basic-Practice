#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int game(char you, char computer) {
  // if draw
  if (you == computer) {
    return -1;
  }

  // if you choose rock
  // and if computer choose paper
  if (you == 's' && computer == 'p') {
    return 0;
  } else if (you == 'p' && computer == 's') {
    return 1;
  }

  // if your choise rock
  // and if computer's choise scissor
  if (you == 's' && computer == 'z') {
    return 0;
  } else if (you == 'z' && computer == 's') {
    return 1;
  }
  // if your choise paper
  // and if computer's choise scissor
  if (you == 'p' && computer == 'z') {
    return 0;
  } else if (you == 'z' && computer == 'p') {
    return 1;
  }
  // handle unexpected inputs
  return -2;
}

int main() {
  // store the tandom number
  int n;
  char you, computer, result;
  // random a number every loop of program
  srand(time(NULL));
  n = rand() % 100;

  // random number to make program choose R/Z/P
  if (n < 33) {
    computer = 's';
  } else if (n > 33 && n < 66) {
    computer = 'z';
  } else {
    computer = 'p';
  }
  printf("\n\n\n\n\t\t\t\tEnter s for STONE, p for PAPER and z for "
         "SCISSOR\n\n\t\t\t\t\t\t\t");

  printf("Your choise:");
  scanf("%c", &you);

  result = game(you, computer);
  if (result == -1) {
    printf("\n\n\t\t\t\tGame Draw!\n");
  } else if (result == 1) {
    printf("\n\n\t\t\t\tYou just lost to the luck XD\n");
  } else if (result == -2) {
    printf("\n\n\t\t\tPlease enter a valid option\n");
  } else {
    printf("\n\n\t\t\t\tYou won the computer!\n");
  }
  printf("\t\t\t\tYou choose: %c and Computer choose: %c\n", you, computer);

  return 0;
}
