public class BaseExpManager {
    public boolean test(CommonRequest commonRequest) {
        int res = method.getIntFlagValueOrDefaultValueByUser(userId,
        ExpFlags.CONST_TEST_NAME, 0);
        String flagName = "test_name_non";
        List<String> flagNameList = Lists.newArrayList("test_name", "test_name_1");
        int res = method.getIntFlagValueOrDefaultValueByUser(userId, flagName, 0);
        int res = method.getFlagValueByDeviceAndFlagNames(userId, flagNameList, 0);
        int res = method.getFlagValueByDeviceAndFlagNames(userId, Lists.newArrayList("test_name", "test_name_1", flagName), 0);
        int res = method.getFlagValueByDeviceAndFlagNames(userId, List.of("test_3"), 0);
        int res = method.getFlagValueByDeviceAndFlagNames(userId, Arrays.asList("test_4", "test_5"), 0);
        String name = flagName;
        int res = method.getIntFlagValueOrDefaultValueByUser(userId, name, 0);
    }

}
