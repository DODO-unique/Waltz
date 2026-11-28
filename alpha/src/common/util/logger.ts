import chalk from 'chalk';

export const info = (...message: any) => {
    console.log(chalk.blue(...message))
}

export const fail = (...message: any) => {
    console.log(chalk.red(...message))
}

export const done = (...message: any) => {
    console.log(chalk.green(...message))
}