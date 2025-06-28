import java.util.*;
import java.util.Scanner;

public class Person {
    public static int totalPersons = 0;

    public String name = "";
    private int age = 0;

    public Person(String name, int age) {
        this.name = name;
        this.age = age;
        totalPersons += 1;
    }

    public static int getTotalPersons() {
        return totalPersons;
    }

    public void greet() {
        System.out.println(String.format("Hello, I'm %s and I'm %s years old", name, age));
    }

    public boolean isAdult() {
        return age >= 18;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    private int getAge() {
        return age;
    }

    private void setAge(int age) {
        this.age = age;
    }

    public static void main(String[] args) {
        Person alice = new Person("Alice", 25);
        Person bob = new Person("Bob", 17);
        alice.greet();
        bob.greet();
        if (alice.isAdult()) {
        System.out.println(String.format("%s is an adult", (alice.name)));
        }
        if (! bob.isAdult()) {
        System.out.println(String.format("%s is a minor", (bob.name)));
        }
        System.out.println(String.format("Total persons: %s", (Person.getTotalPersons())));
    }
}