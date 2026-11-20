package com.awd.job.health;

import com.awd.job.repository.JobRepository;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

/**
 * Indicateur de sante personnalise : verifie que la table "job" est lisible.
 * Apparait dans /actuator/health sous la cle "jobsTable".
 */
@Component
public class JobsTableHealthIndicator implements HealthIndicator {

    private final JobRepository jobRepository;

    public JobsTableHealthIndicator(JobRepository jobRepository) {
        this.jobRepository = jobRepository;
    }

    @Override
    public Health health() {
        try {
            long count = jobRepository.count();
            return Health.up()
                    .withDetail("table", "job")
                    .withDetail("nombreOffres", count)
                    .build();
        } catch (Exception e) {
            return Health.down(e)
                    .withDetail("table", "job")
                    .withDetail("raison", "Table job illisible")
                    .build();
        }
    }
}
