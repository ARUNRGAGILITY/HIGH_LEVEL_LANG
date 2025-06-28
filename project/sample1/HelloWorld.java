import java.util.*;
import java.util.Scanner;

public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        System.out.println("Check this javax");
        System.out.println("Welcome to Pseudo Java!");
        var name = "Alice";
        var age = 25;
        System.out.println(String.format("Hello %s, you are %s years old", name, age));
        System.out.println(String.format("Next year you'll be %s", (age + 1)));
    }
}
