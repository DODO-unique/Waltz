import chalk from 'chalk';

export const log = (...message: any) => {
    console.log(chalk.blue(...message))
}

export const error = (...message: any) => {
    console.log(chalk.red(...message))
}

export const success = (...message: any) => {
    console.log(chalk.green(...message))
}