# LLM Prompts for Speaker and Church Descriptions

## 🎯 Speaker Description Prompt

```
You are creating detailed speaker descriptions for an AI-powered church recommendation system. These descriptions will be used to generate semantic embeddings that match users with compatible speakers based on teaching style, content focus, and ministry approach.

**Context:** The AI system uses these descriptions to understand each speaker's unique characteristics and match them with users who have specific preferences for teaching style (warm/conversational, passionate/high-energy, calm/reflective), Bible approach (scripture-focused, application-focused, balanced), and worship environment (traditional, contemporary, blended).

**Task:** Create a comprehensive speaker description (200-300 words) that captures their unique ministry style, personality, content themes, and approach to teaching.

**Input Information:**
- Name: [Speaker Name]
- Title: [Current Title/Position]
- Current Bio: [Existing short bio]
- Church Affiliation: [Church name and denomination]
- Teaching Style: [Warm/Conversational, Passionate/High-Energy, or Calm/Reflective]
- Bible Approach: [Scripture-focused, Application-focused, or Balanced]
- Environment: [Traditional, Contemporary, or Blended]
- Years of Service: [If known]
- Notable Works: [Books, programs, ministries - if known]

**Description Structure:**
1. **Opening Statement** (1-2 sentences): Who they are and their primary ministry focus
2. **Teaching Style & Personality** (2-3 sentences): How they communicate, their energy level, relatability
3. **Content & Biblical Approach** (2-3 sentences): What they teach about, how they handle scripture
4. **Ministry Impact & Audience** (2-3 sentences): Who they connect with, their ministry's reach/impact
5. **Unique Characteristics** (1-2 sentences): What makes them distinctive, special gifts/approaches

**Key Elements to Include:**
- Specific adjectives that capture their personality and style
- Content themes they frequently address (family, leadership, spiritual growth, etc.)
- How they make complex concepts accessible
- Their heart for specific audiences (women, families, young adults, etc.)
- Ministry philosophy and core values
- Communication style and delivery approach

**Example Output:**
Beth Moore is a beloved Bible teacher and author known for her passionate, authentic approach to women's ministry and biblical study. With over three decades of ministry experience, she has touched millions of lives through her in-depth Bible studies and heartfelt teaching.

Moore's teaching style is warm and conversational, creating an intimate atmosphere even in large venues. She has a remarkable gift for making ancient biblical truths feel immediate and relevant, often sharing personal struggles and victories that resonate deeply with her audience. Her approach combines rigorous scriptural study with practical life application, helping women understand not just what the Bible says, but how to live it out daily.

Known for her focus on helping women discover their identity in Christ, Moore addresses themes of spiritual warfare, overcoming insecurity, and living boldly in faith. She creates a safe space for vulnerability while challenging her audience to grow deeper in their relationship with God. Her ministry particularly resonates with women seeking authentic, biblically-grounded teaching that speaks to real-life challenges.

Moore's unique ability to blend scholarly biblical insight with relatable storytelling sets her apart. She approaches scripture with both reverence and accessibility, making complex theological concepts understandable while maintaining their depth and power. Her heart for women's spiritual growth and her transparent, encouraging style have made her one of the most trusted voices in contemporary Christian women's ministry.

**Generate a similar description for:** [Insert speaker details here]
```

## 🏛️ Church Description Prompt

```
You are creating detailed church descriptions for an AI-powered recommendation system that matches users with compatible churches based on worship style, community culture, theological approach, and ministry focus.

**Context:** The AI system uses these descriptions to understand each church's unique characteristics and match them with users who have specific preferences for worship environment (traditional, contemporary, blended), community size, denominational approach, and ministry priorities.

**Task:** Create a comprehensive church description (250-350 words) that captures their worship style, community culture, theological approach, ministry focus, and unique characteristics.

**Input Information:**
- Name: [Church Name]
- Denomination: [Denomination]
- Current Description: [Existing short description]
- Location: [City, State]
- Size: [Membership count/weekly attendance]
- Founded: [Year founded, if known]
- Senior Pastor: [Name and brief info]
- Worship Style: [Traditional, Contemporary, or Blended]
- Notable Programs: [If known]
- Community Focus: [If known]

**Description Structure:**
1. **Church Identity** (2-3 sentences): What they're known for, their mission/vision
2. **Worship Experience** (2-3 sentences): Service style, music, atmosphere, format
3. **Teaching & Theology** (2-3 sentences): Preaching style, biblical approach, theological emphasis
4. **Community & Culture** (2-3 sentences): Church personality, how members interact, inclusivity
5. **Ministry & Outreach** (2-3 sentences): Programs, community involvement, service focus
6. **Unique Characteristics** (1-2 sentences): What sets them apart, special strengths

**Key Elements to Include:**
- Worship atmosphere and energy level
- Music style and production quality
- Preaching approach (expository, topical, practical, etc.)
- Community size feel (intimate, mid-size, large, mega-church)
- Demographic they primarily serve
- Core values and ministry philosophy
- Outreach and service emphasis
- Family/children's ministry approach
- Small group/community connection opportunities

**Example Output:**
Life.Church is a multi-site, contemporary church known for its innovative approach to ministry and strong emphasis on community connection. Founded by Craig Groeschel, this non-denominational church has grown to serve over 70,000 weekly attendees across multiple locations, while maintaining a personal, welcoming atmosphere that makes everyone feel like family.

The worship experience at Life.Church is contemporary and engaging, featuring modern music, high-quality production, and a casual, come-as-you-are atmosphere. Services are designed to be accessible to both longtime believers and those new to faith, with clear, practical teaching that connects biblical truth to everyday life. The environment is warm and inviting, with excellent children's programs and a strong emphasis on creating authentic relationships.

Teaching at Life.Church focuses on practical, life-applicable messages that help people navigate real-world challenges through biblical principles. The preaching style is conversational and relatable, often incorporating multimedia elements and real-life stories. The church emphasizes grace, authenticity, and spiritual growth, creating a safe space for people to explore faith and ask questions.

Community is at the heart of Life.Church's identity, with extensive small group networks and volunteer opportunities that help members build meaningful connections. The church is known for its generous spirit, both in serving the local community and supporting global missions. Their innovative use of technology, including a popular Bible app and online resources, demonstrates their commitment to meeting people where they are.

Life.Church attracts families, young professionals, and individuals seeking a contemporary worship experience with solid biblical teaching. Their multi-generational approach and emphasis on practical spirituality make them particularly appealing to those who want to grow in faith while staying connected to modern life.

**Generate a similar description for:** [Insert church details here]
```

## 📋 Quick Reference Templates

### Speaker Description Checklist:
- [ ] Teaching personality (warm, passionate, calm)
- [ ] Content themes and focus areas
- [ ] Target audience and ministry heart
- [ ] Biblical approach and depth level
- [ ] Communication style and delivery
- [ ] Years of experience and credibility
- [ ] Unique gifts and characteristics
- [ ] Ministry impact and reach

### Church Description Checklist:
- [ ] Worship style and atmosphere
- [ ] Music and service format
- [ ] Preaching approach and theology
- [ ] Community size and culture
- [ ] Demographics and target audience
- [ ] Core values and mission focus
- [ ] Programs and ministries offered
- [ ] Outreach and service emphasis
- [ ] What makes them unique

## 🎯 Usage Instructions

1. **For Speakers:** Use the speaker prompt with your existing speaker data
2. **For Churches:** Use the church prompt with your existing church data
3. **Batch Processing:** You can process multiple speakers/churches by providing the template with different input data
4. **Quality Check:** Ensure descriptions are 200-350 words and include all key elements
5. **Database Update:** Use the generated descriptions to update your `speakers.bio` and `churches.description` fields

These rich descriptions will dramatically improve your AI embedding quality and recommendation accuracy!
