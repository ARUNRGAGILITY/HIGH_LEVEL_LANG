import java.util.*;
import java.util.Scanner;

public class LaunchStudent {
    public static void main(String[] args) {
        System.out.println(String.format("Welcome to %s", (Student.getSchoolName())));
        Student alice = new Student("S001", "Alice Johnson");
        Student bob = new Student("S002", "Bob Smith");
        alice.addGrade("Math", 92.5);
        alice.addGrade("Science", 88.0);
        alice.addGrade("English", 95.0);
        bob.addGrade("Math", 78.5);
        bob.addGrade("Science", 82.0);
        bob.addGrade("History", 90.0);
        alice.printTranscript();
        bob.printTranscript();
        System.out.println(String.format("Total students: %s", (Student.getTotalStudents())));
    }
}