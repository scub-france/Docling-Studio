import com.intuit.karate.junit5.Karate;

class UIRunner {

    @Karate.Test
    Karate testAll() {
        return Karate.run("classpath:documents", "classpath:analyses", "classpath:navigation", "classpath:workflows")
                .relativeTo(getClass());
    }

    @Karate.Test
    Karate testCritical() {
        return Karate.run("classpath:documents", "classpath:analyses")
                .tags("@critical")
                .relativeTo(getClass());
    }

    @Karate.Test
    Karate testLocal() {
        return Karate.run("classpath:documents", "classpath:analyses", "classpath:navigation", "classpath:workflows")
                .tags("@ui")
                .relativeTo(getClass());
    }
}
