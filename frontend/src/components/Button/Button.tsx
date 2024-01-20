import classes from './Button.module.css';

// interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
//   title: string;
// }

function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={classes.button} {...props}>
      {props.children}
    </button>
  );
}

export default Button;
