import java.util.*;
import java.util.Scanner;

public class Student {
    public static int totalStudents = 0;
    private static String schoolName = "Tech University";

    public String studentId;
    public String name;
    private ArrayList<Double> grades = new ArrayList<Double>();
    protected ArrayList<String> courses = new ArrayList<String>();
    double gpa;

    public Student(String studentId, String name) {
        this.studentId = studentId;
        this.name = name;
        this.grades = new ArrayList<Double>();
        this.courses = new ArrayList<String>();
        this.gpa = 0.0;
        totalStudents += 1;
    }

    public static int getTotalStudents() {
        return totalStudents;
    }

    public static String getSchoolName() {
        return schoolName;
    }

    public void addGrade(String course, double grade) {
        courses.add(course);
        grades.add(grade);
        updateGPA();
        System.out.println(String.format("Added grade %s for course %s", grade, course));
    }

    public double getGPA() {
        return gpa;
    }

    private void updateGPA() {
        if (grades.size() == 0) {
        gpa = 0.0;
        return;
        }
        double total = 0.0;
        for (var grade : grades) {
        total += grade;
        }
        gpa = total / grades.size();
    }

    public void printTranscript() {
        System.out.println("=== TRANSCRIPT ===");
        System.out.println(String.format("Student: %s (ID: %s)", name, studentId));
        System.out.println(String.format("School: %s", (getSchoolName())));
        System.out.println(String.format("Courses: %s", (courses.size())));
        System.out.println(String.format("GPA: %.2f", gpa));
        for (int i = 0; i < courses.size(); i++) {
        String courseName = courses.get(i);
        double grade = grades.get(i);
        System.out.println(String.format("%s: %s", courseName, grade));
        }
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    protected String getStudentid() {
        return studentId;
    }

    protected void setStudentid(String studentId) {
        this.studentId = studentId;
    }

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