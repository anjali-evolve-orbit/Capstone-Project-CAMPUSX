-- ============================================================
-- CAMPUSX — Discover People Behind the Work System
-- Realistic Seed Data for St. John Campus & Extensible System
-- ============================================================

USE `campusx_db`;

-- 1. SEED CAMPUSES
INSERT INTO `campuses` (`id`, `name`, `location`, `description`) VALUES
(1, 'St. John Technical & Educational Campus', 'Palghar, Maharashtra, India', 'Premier multidisciplinary academic campus established by Aldel Education Trust hosting engineering, pharmacy, humanities, and research institutes.')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 2. SEED INSTITUTIONS
INSERT INTO `institutions` (`id`, `campus_id`, `name`, `code`, `is_custom`) VALUES
(1, 1, 'St. John College of Engineering & Management', 'SJCEM', FALSE),
(2, 1, 'St. John Institute of Pharmacy & Research', 'SJIPR', FALSE),
(3, 1, 'St. John College of Humanities & Sciences', 'SJCHS', FALSE),
(999, 1, 'Other Institution', 'OTHER', TRUE)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 3. SEED DEPARTMENTS
INSERT INTO `departments` (`id`, `institution_id`, `name`, `code`, `is_custom`) VALUES
-- SJCEM Departments
(1, 1, 'Computer Engineering', 'COMP', FALSE),
(2, 1, 'Information Technology', 'IT', FALSE),
(3, 1, 'Artificial Intelligence and Data Science', 'AIDS', FALSE),
(4, 1, 'Electronics and Telecommunication', 'EXTC', FALSE),
(5, 1, 'Civil Engineering', 'CIVIL', FALSE),
(6, 1, 'Mechanical Engineering', 'MECH', FALSE),
(991, 1, 'Other Department / Program', 'OTHER_SJCEM', TRUE),

-- SJIPR Departments
(7, 2, 'Pharmaceutics', 'PCEUT', FALSE),
(8, 2, 'Pharmaceutical Chemistry', 'PCHEM', FALSE),
(9, 2, 'Pharmacology', 'PCOL', FALSE),
(10, 2, 'Pharmacognosy', 'PCOG', FALSE),
(992, 2, 'Other Department / Program', 'OTHER_SJIPR', TRUE),

-- SJCHS Departments
(11, 3, 'Computer Science', 'CS_CHS', FALSE),
(12, 3, 'Biotechnology', 'BIOTECH', FALSE),
(13, 3, 'Management Studies', 'BMS', FALSE),
(993, 3, 'Other Department / Program', 'OTHER_SJCHS', TRUE),

-- Generic Other
(999, 999, 'Other Department / Program', 'OTHER_GEN', TRUE)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 4. SEED RESEARCH AREAS
INSERT INTO `research_areas` (`id`, `name`, `description`, `icon_name`) VALUES
(1, 'Artificial Intelligence', 'Study of intelligent agents, neural reasoning, cognitive computing, and autonomous agents.', 'Brain'),
(2, 'Machine Learning', 'Statistical learning models, deep learning architectures, reinforcement learning, and predictive analytics.', 'Cpu'),
(3, 'Cybersecurity', 'Network security protocols, cryptographic systems, vulnerability assessment, threat intelligence, and zero trust.', 'ShieldCheck'),
(4, 'Data Science', 'Big data architectures, automated feature engineering, spatial data pipelines, and data-driven discovery.', 'Database'),
(5, 'Internet of Things', 'Smart embedded sensors, low-power edge gateways, industrial IoT telemetry, and smart campus devices.', 'Wifi'),
(6, 'Computer Networks', 'Software-defined networking, 5G/6G wireless communication protocols, routing optimization, and SDN.', 'Network'),
(7, 'Software Engineering', 'Automated testing frameworks, distributed microservice design, DevOps, and code intelligence.', 'Code'),
(8, 'Natural Language Processing', 'Large language models, semantic information retrieval, cross-lingual translation, and sentiment extraction.', 'MessageSquare'),
(9, 'Cloud & Distributed Systems', 'Serverless computing, consensus algorithms, multi-tenant cloud orchestration, and fault tolerance.', 'Cloud'),
(10, 'Healthcare & Biomedical Informatics', 'Medical imaging analysis, computational drug discovery, genomics data modeling, and clinical decision support.', 'Activity')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 5. SEED RESEARCHERS
INSERT INTO `researchers` (`id`, `user_id`, `name`, `designation`, `institution_id`, `department_id`, `bio`, `avatar_color`, `citation_count`, `h_index`, `email`, `website`) VALUES
(1, NULL, 'Dr. Nilesh Patil', 'Professor & Head of Research', 1, 1, 'Head of Research at SJCEM focusing on Artificial Intelligence, distributed machine learning, and explainable AI in academic workflows.', '#1E4E8C', 485, 14, 'nilesh.patil@campusx.edu', 'https://campusx.edu/researchers/npatil'),
(2, NULL, 'Dr. Sneha More', 'Associate Professor', 1, 2, 'Specializes in Cyber-Physical Systems security, anomaly detection in encrypted traffic, and applied cryptography.', '#3B82F6', 320, 11, 'sneha.more@campusx.edu', 'https://campusx.edu/researchers/smore'),
(3, NULL, 'Dr. Rahul Varma', 'Assistant Professor', 1, 3, 'Deep learning researcher working on multi-modal computer vision and federated learning applications for smart cities.', '#6C5CE7', 215, 8, 'rahul.varma@campusx.edu', 'https://campusx.edu/researchers/rvarma'),
(4, NULL, 'Prof. Anita Deshmukh', 'Assistant Professor', 1, 1, 'Focuses on Data Science, Big Data analytics, and knowledge graph engineering for institutional discovery.', '#22C7E8', 190, 7, 'anita.deshmukh@campusx.edu', 'https://campusx.edu/researchers/adeshmukh'),
(5, NULL, 'Dr. Rajesh Kulkarni', 'Professor & Dean R&D', 1, 4, 'Pioneering researcher in IoT sensor networks, embedded wireless sensor nodes, and 5G edge computing.', '#0B1F33', 610, 18, 'rajesh.kulkarni@campusx.edu', 'https://campusx.edu/researchers/rkulkarni'),
(6, NULL, 'Dr. Priya Mehta', 'Associate Professor', 2, 7, 'Research focuses on Computational Drug Delivery systems, nano-formulations, and AI-assisted pharmacokinetic analysis.', '#10B981', 340, 12, 'priya.mehta@campusx.edu', 'https://campusx.edu/researchers/pmehta'),
(7, NULL, 'Dr. Vikram Joshi', 'Assistant Professor', 2, 8, 'Investigating computational molecular docking, cheminformatics, and predictive ADMET modeling using machine learning.', '#F59E0B', 175, 7, 'vikram.joshi@campusx.edu', 'https://campusx.edu/researchers/vjoshi'),
(8, NULL, 'Dr. Kavita Nair', 'Associate Professor', 3, 11, 'Working on Natural Language Processing, semantic web graphs, and cross-disciplinary educational data mining.', '#EC4899', 245, 9, 'kavita.nair@campusx.edu', 'https://campusx.edu/researchers/knair'),
(9, NULL, 'Prof. Amit Sawant', 'Assistant Professor', 1, 2, 'Expert in Cloud & Distributed Systems, microservices resilience patterns, and edge cache optimization.', '#8B5CF6', 160, 6, 'amit.sawant@campusx.edu', 'https://campusx.edu/researchers/asawant'),
(10, NULL, 'Prof. Neha Gupta', 'Research Scholar & Lecturer', 1, 3, 'Conducting research on Deep Reinforcement Learning for autonomous navigation and edge robotics.', '#14B8A6', 110, 5, 'neha.gupta@campusx.edu', 'https://campusx.edu/researchers/ngupta'),
(11, NULL, 'Dr. Sandeep Thakur', 'Professor', 1, 1, 'Veteran academic researcher in Software Engineering metrics, automated defect prediction, and code analysis.', '#64748B', 430, 13, 'sandeep.thakur@campusx.edu', 'https://campusx.edu/researchers/sthakur'),
(12, NULL, 'Dr. Meera Iyer', 'Associate Professor', 3, 12, 'Interdisciplinary research in Bioinformatics, genomic sequence analysis, and biomedical text mining.', '#06B6D4', 280, 10, 'meera.iyer@campusx.edu', 'https://campusx.edu/researchers/miyer')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 6. SEED RESEARCHER_AREAS
INSERT INTO `researcher_areas` (`researcher_id`, `research_area_id`) VALUES
-- Dr. Nilesh Patil (AI, ML, Data Science)
(1, 1), (1, 2), (1, 4),
-- Dr. Sneha More (Cybersecurity, Computer Networks)
(2, 3), (2, 6),
-- Dr. Rahul Varma (Machine Learning, AI, Computer Networks)
(3, 2), (3, 1), (3, 6),
-- Prof. Anita Deshmukh (Data Science, AI, NLP)
(4, 4), (4, 1), (4, 8),
-- Dr. Rajesh Kulkarni (IoT, Computer Networks, Cloud)
(5, 5), (5, 6), (5, 9),
-- Dr. Priya Mehta (Healthcare Informatics, Data Science)
(6, 10), (6, 4),
-- Dr. Vikram Joshi (Healthcare Informatics, Machine Learning)
(7, 10), (7, 2),
-- Dr. Kavita Nair (NLP, AI, Data Science)
(8, 8), (8, 1), (8, 4),
-- Prof. Amit Sawant (Cloud & Distributed Systems, Software Engineering)
(9, 9), (9, 7),
-- Prof. Neha Gupta (Machine Learning, IoT)
(10, 2), (10, 5),
-- Dr. Sandeep Thakur (Software Engineering, Data Science)
(11, 7), (11, 4),
-- Dr. Meera Iyer (Healthcare Informatics, AI, NLP)
(12, 10), (12, 1), (12, 8)
ON DUPLICATE KEY UPDATE `research_area_id`=VALUES(`research_area_id`);

-- 7. SEED PAPERS
INSERT INTO `papers` (`id`, `title`, `abstract`, `publication_year`, `venue`, `citation_count`, `doi`, `pdf_url`, `primary_area_id`) VALUES
(1, 'Scalable Graph Neural Networks for Academic Collaboration Discovery', 'We propose an inductive representation learning framework across heterogeneous institutional academic graphs to discover multi-hop research collaborations and emergent domain intersections.', 2024, 'IEEE Transactions on Knowledge and Data Engineering', 42, '10.1109/TKDE.2024.10452', 'https://campusx.edu/papers/p1.pdf', 1),
(2, 'Zero-Trust Security Protocols for Multi-Campus Internet of Things Gateways', 'This study introduces an adaptive intrusion detection mechanism utilizing localized lightweight autoencoders deployed directly onto low-power edge gateways across campus subnets.', 2023, 'ACM Transactions on Cyber-Physical Systems', 38, '10.1145/3589123', 'https://campusx.edu/papers/p2.pdf', 3),
(3, 'Federated Optimization in Resource-Constrained Academic Edge Clusters', 'We analyze communication-efficient federated stochastic gradient descent under heterogeneous compute availability and intermittent campus network connectivity.', 2024, 'Journal of Systems Architecture', 29, '10.1016/j.sysarc.2024.103', 'https://campusx.edu/papers/p3.pdf', 2),
(4, 'Automated Molecular Docking and Affinity Prediction via Graph Attention Networks', 'A deep graph attention network architecture for predicting ligand-protein binding poses, accelerating target validation in computational pharmacological workflows.', 2023, 'Bioinformatics & Drug Discovery Letters', 51, '10.1093/bioinf/btad410', 'https://campusx.edu/papers/p4.pdf', 10),
(5, 'Energy-Efficient Telemetry Collection in Large-Scale Smart Campus Sensors', 'Investigates dynamic sleep scheduling algorithms for LoRaWAN and BLE sensor nodes installed in institutional buildings for environmental monitoring.', 2022, 'IEEE Internet of Things Journal', 67, '10.1109/JIOT.2022.3190', 'https://campusx.edu/papers/p5.pdf', 5),
(6, 'Cross-Lingual Semantic Retrieval of Institutional Scholarly Repositories', 'Demonstrates transformer-based semantic search strategies that outperform lexical BM25 rankings for multi-disciplinary institutional academic theses.', 2024, 'Information Sciences', 33, '10.1016/j.ins.2024.120', 'https://campusx.edu/papers/p6.pdf', 8),
(7, 'Microservices Fault Injection and Resilience Verification in Educational Clouds', 'Examines automated chaos engineering probes to evaluate service mesh failover latencies and data consistency under simulated network partitions.', 2023, 'Software: Practice and Experience', 24, '10.1002/spe.3175', 'https://campusx.edu/papers/p7.pdf', 7),
(8, 'Adversarial Defense for Deep Learning Models in Encrypted Campus Traffic', 'Presents a robust feature-masking defense against evasion attacks on neural traffic classifiers inspecting TLS 1.3 telemetry.', 2023, 'Computers & Security', 45, '10.1016/j.cose.2023.103', 'https://campusx.edu/papers/p8.pdf', 3),
(9, 'Decentralized Identity Verification for Cross-Institutional Credit Transfer', 'Introduces a permissioned distributed ledger architecture verifying student credentials and academic research contributions without centralized authority.', 2022, 'IEEE Access', 58, '10.1109/ACCESS.2022.3168', 'https://campusx.edu/papers/p9.pdf', 6),
(10, 'Deep Reinforcement Learning for Real-Time Packet Routing Optimization in 5G Campus Slices', 'Investigates policy gradient reinforcement learning algorithms implemented on OpenFlow switches to guarantee low-latency QoS for laboratory video streams.', 2024, 'Computer Networks', 36, '10.1016/j.comnet.2024.110', 'https://campusx.edu/papers/p10.pdf', 6),
(11, 'Biomedical Named Entity Recognition in Clinical Case Notes using Compact Ensembles', 'Proposes knowledge-distilled bidirectional language representations for identifying pharmaceutical adverse effects and compound interactions.', 2023, 'Journal of Biomedical Informatics', 39, '10.1016/j.jbi.2023.104', 'https://campusx.edu/papers/p11.pdf', 10),
(12, 'Automated Static Code Smell Detection in Student Submissions using Graph Representations', 'Evaluates Abstract Syntax Tree transformations mapped into directed acyclic graphs to evaluate algorithmic efficiency and maintainability.', 2022, 'IEEE Transactions on Education', 54, '10.1109/TE.2022.3155', 'https://campusx.edu/papers/p12.pdf', 7)
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

-- 8. SEED PAPER_AUTHORS
INSERT INTO `paper_authors` (`paper_id`, `researcher_id`, `author_order`) VALUES
-- Paper 1: Patil, Deshmukh, Nair
(1, 1, 1), (1, 4, 2), (1, 8, 3),
-- Paper 2: More, Kulkarni
(2, 2, 1), (2, 5, 2),
-- Paper 3: Varma, Patil, Gupta
(3, 3, 1), (3, 1, 2), (3, 10, 3),
-- Paper 4: Joshi, Mehta, Varma
(4, 7, 1), (4, 6, 2), (4, 3, 3),
-- Paper 5: Kulkarni, Gupta
(5, 5, 1), (5, 10, 2),
-- Paper 6: Nair, Deshmukh
(6, 8, 1), (6, 4, 2),
-- Paper 7: Sawant, Thakur
(7, 9, 1), (7, 11, 2),
-- Paper 8: More, Varma
(8, 2, 1), (8, 3, 2),
-- Paper 9: More, Sawant
(9, 2, 1), (9, 9, 2),
-- Paper 10: Varma, Kulkarni
(10, 3, 1), (10, 5, 2),
-- Paper 11: Iyer, Mehta, Nair
(11, 12, 1), (11, 6, 2), (11, 8, 3),
-- Paper 12: Thakur, Patil
(12, 11, 1), (12, 1, 2)
ON DUPLICATE KEY UPDATE `author_order`=VALUES(`author_order`);

-- 9. SEED PAPER_AREAS
INSERT INTO `paper_areas` (`paper_id`, `research_area_id`) VALUES
(1, 1), (1, 4),
(2, 3), (2, 5),
(3, 2), (3, 9),
(4, 10), (4, 2),
(5, 5), (5, 6),
(6, 8), (6, 4),
(7, 7), (7, 9),
(8, 3), (8, 2),
(9, 6), (9, 9),
(10, 6), (10, 1),
(11, 10), (11, 8),
(12, 7), (12, 4)
ON DUPLICATE KEY UPDATE `research_area_id`=VALUES(`research_area_id`);

-- 10. SEED COLLABORATIONS (EXPLICIT GRAPH EDGES FOR BFS/DFS/NETWORK)
INSERT INTO `collaborations` (`researcher1_id`, `researcher2_id`, `paper_count`, `joint_papers_desc`) VALUES
(1, 4, 2, 'Joint publications on Graph Neural Networks and Knowledge Graph Discovery in academic systems.'),
(1, 3, 3, 'Co-authored papers on Federated Learning and deep neural model optimization.'),
(1, 8, 1, 'Collaborative work on multi-disciplinary institutional academic graphs.'),
(1, 11, 2, 'Inter-departmental research on automated defect prediction and code complexity.'),
(2, 5, 2, 'Joint investigations on IoT edge security and lightweight cryptographic gateways.'),
(2, 3, 2, 'Research on adversarial defense in deep learning classifiers on encrypted networks.'),
(2, 9, 1, 'Collaborative paper on decentralized identity and cloud verification.'),
(3, 10, 2, 'Co-advised research on reinforcement learning and smart edge robotics.'),
(3, 5, 2, 'Joint research on 5G routing optimization and IoT edge communication.'),
(3, 7, 1, 'Inter-institutional collaboration bridging machine learning algorithms with molecular docking.'),
(4, 8, 2, 'Cross-college work on NLP, semantic retrieval, and scholarly repositories.'),
(5, 10, 2, 'Smart campus telemetry and low-power IoT node deployments.'),
(6, 7, 3, 'Pharmacology and chemistry collaborative papers on computational drug formulation.'),
(6, 12, 2, 'Inter-institutional research in biomedical informatics and adverse compound extraction.'),
(7, 12, 1, 'Bioinformatics and molecular screening algorithms.'),
(8, 12, 1, 'Bio-NLP and clinical entity extraction models.'),
(9, 11, 2, 'Software architecture resilience and microservice fault injection.')
ON DUPLICATE KEY UPDATE `paper_count`=VALUES(`paper_count`);

-- 11. SEED COMMUNITIES
INSERT INTO `communities` (`id`, `name`, `description`, `institution_id`, `category`, `member_count`) VALUES
(1, 'AI & Intelligent Systems Lab', 'Research group dedicated to foundation models, knowledge representations, and autonomous learning systems across campus.', 1, 'Research Group', 34),
(2, 'Cyber Defense & Security Wing', 'Technical community researching cryptography, network vulnerability assessment, and zero-trust systems.', 1, 'Technical Community', 28),
(3, 'Smart Campus & IoT Innovation Cluster', 'Hands-on interdisciplinary research group deploying environmental telemetry and edge gateways across campus facilities.', 1, 'Research Group', 22),
(4, 'Computational Drug Discovery Consortium', 'Interdisciplinary collaboration between engineering, pharmaceutical, and biological sciences researchers for in-silico screening.', 2, 'Academic Group', 18),
(5, 'Data Science & Knowledge Graph Forum', 'Departmental and campus-wide collective analyzing educational data, bibliometrics, and graph algorithms.', 1, 'Department Research Community', 30),
(6, 'Biomedical Informatics Research Circle', 'Focuses on healthcare datasets, genomic sequence pattern matching, and clinical text mining.', 3, 'Interest-based Academic Group', 16),
(7, 'Distributed Systems & Cloud Architecture Group', 'Explores edge cloud computing, microservice resilience, and serverless architectures.', 1, 'Technical Community', 25),
(8, 'Women in Research & STEM Alliance', 'Academic network supporting female researchers, students, and faculty across technical disciplines.', 1, 'Academic Group', 42)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 12. SEED COMMUNITY_MEMBERS
INSERT INTO `community_members` (`community_id`, `researcher_id`, `role`) VALUES
(1, 1, 'Lead Faculty Advisor'),
(1, 3, 'Co-Advisor'),
(1, 4, 'Senior Researcher'),
(1, 10, 'Member'),
(2, 2, 'Faculty Lead'),
(2, 9, 'Technical Advisor'),
(3, 5, 'Principal Investigator'),
(3, 10, 'Member'),
(4, 6, 'Lead Researcher'),
(4, 7, 'Member'),
(4, 3, 'Technical Collaborator'),
(5, 4, 'Coordinator'),
(5, 1, 'Advisor'),
(5, 8, 'Member'),
(6, 12, 'Faculty Lead'),
(6, 6, 'Collaborator'),
(7, 9, 'Lead'),
(7, 11, 'Senior Member'),
(8, 2, 'President'),
(8, 4, 'Executive Member'),
(8, 6, 'Member'),
(8, 8, 'Member'),
(8, 12, 'Member')
ON DUPLICATE KEY UPDATE `role`=VALUES(`role`);

-- 13. SEED INITIAL DEMO USERS
-- Default password for all seed demo users: 'CampusX@2026'
INSERT INTO `users` (`id`, `full_name`, `email`, `password_hash`, `role`, `campus_id`, `institution_id`, `department_id`) VALUES
(1, 'Demo Student', 'student@campusx.edu', '4b1e328d1a0b2d5969a0c401b077decd94103b7adbe35dd7372e956b85eec496', 'Student', 1, 1, 1),
(2, 'Dr. Nilesh Patil', 'nilesh.patil@campusx.edu', '4b1e328d1a0b2d5969a0c401b077decd94103b7adbe35dd7372e956b85eec496', 'Faculty', 1, 1, 1),
(3, 'Dr. Sneha More', 'sneha.more@campusx.edu', '4b1e328d1a0b2d5969a0c401b077decd94103b7adbe35dd7372e956b85eec496', 'Researcher', 1, 1, 2),
(11, 'Dr. Sandeep Thakur', 'sandeep.thakur@campusx.edu', '4b1e328d1a0b2d5969a0c401b077decd94103b7adbe35dd7372e956b85eec496', 'Faculty', 1, 1, 1)
ON DUPLICATE KEY UPDATE `email`=VALUES(`email`), `password_hash`=VALUES(`password_hash`);

-- 14. SEED SKILLS
INSERT INTO `skills` (`id`, `name`) VALUES
(1, 'C++'),
(2, 'Python'),
(3, 'MySQL'),
(4, 'FastAPI'),
(5, 'Machine Learning'),
(6, 'Deep Learning'),
(7, 'Natural Language Processing'),
(8, 'Computer Vision'),
(9, 'Data Science'),
(10, 'Data Structures & Algorithms'),
(11, 'Graph Algorithms'),
(12, 'Cybersecurity'),
(13, 'Network Security'),
(14, 'Cryptography'),
(15, 'Cloud Computing'),
(16, 'Distributed Systems'),
(17, 'Internet of Things (IoT)'),
(18, 'Embedded Systems'),
(19, 'Bioinformatics'),
(20, 'Molecular Docking'),
(21, 'Cheminformatics'),
(22, 'Software Engineering'),
(23, 'React'),
(24, 'PyTorch'),
(25, 'TensorFlow'),
(26, 'Docker & Kubernetes'),
(27, 'Microservices'),
(28, 'Big Data Analytics'),
(29, 'Reinforcement Learning'),
(30, 'Wireless Sensor Networks')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 15. SEED RESEARCHER_SKILLS
INSERT INTO `researcher_skills` (`researcher_id`, `skill_id`) VALUES
-- Dr. Nilesh Patil
(1, 2), (1, 5), (1, 6), (1, 10), (1, 11), (1, 24),
-- Dr. Sneha More
(2, 2), (2, 12), (2, 13), (2, 14), (2, 17),
-- Dr. Rahul Varma
(3, 2), (3, 5), (3, 6), (3, 8), (3, 24),
-- Prof. Anita Deshmukh
(4, 2), (4, 3), (4, 7), (4, 9), (4, 28),
-- Dr. Rajesh Kulkarni
(5, 1), (5, 17), (5, 18), (5, 30),
-- Dr. Priya Mehta
(6, 19), (6, 20), (6, 21), (6, 9),
-- Dr. Vikram Joshi
(7, 2), (7, 5), (7, 20), (7, 21),
-- Dr. Kavita Nair
(8, 2), (8, 7), (8, 9), (8, 10), (8, 11),
-- Prof. Amit Sawant
(9, 2), (9, 15), (9, 16), (9, 26), (9, 27),
-- Prof. Neha Gupta
(10, 2), (10, 5), (10, 17), (10, 29),
-- Dr. Sandeep Thakur
(11, 2), (11, 3), (11, 4), (11, 10), (11, 22),
-- Dr. Meera Iyer
(12, 2), (12, 6), (12, 7), (12, 19)
ON DUPLICATE KEY UPDATE `skill_id`=VALUES(`skill_id`);
