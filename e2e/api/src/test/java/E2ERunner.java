import com.intuit.karate.junit5.Karate;

class E2ERunner {

    @Karate.Test
    Karate testAll() {
        return Karate.run("classpath:health", "classpath:documents", "classpath:analyses", "classpath:workflows", "classpath:ingestion")
                .relativeTo(getClass());
    }

    @Karate.Test
    Karate testIngestion() {
        return Karate.run("classpath:ingestion")
                .tags("@ingestion")
                .relativeTo(getClass());
    }

    @Karate.Test
    Karate testSmoke() {
        return Karate.run("classpath:health")
                .tags("@smoke")
                .relativeTo(getClass());
    }
}
